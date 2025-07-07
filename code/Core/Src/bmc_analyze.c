#include "bmc_analyze.h"

static int is_training_code(const uint8_t *bits, int len) {
    // 这里检测是否为交替序列，至少前60bit
    for (int i = 0; i < len - 1; i++) {
        if (bits[i] == bits[i+1]) {
            return 0;  // 连续两个bit相同，不是典型训练码
        }
    }
    return 1; // 前面所有相邻bit都交替，极大概率是训练码
}

// 每5个bit转为一个字节，高3位补0
static void pack_5bit_to_byte(const uint8_t *bit_stream, int bit_len, uint8_t *out_bytes, int *out_len) {
    int byte_count = 0;
    for (int i = 0; i + 4 < bit_len; i += 5) {
        uint8_t val5b = 0;
        for (int j = 0; j < 5; j++) {
            val5b |= (bit_stream[i + j] & 1) << j; // LSB first
        }
        out_bytes[byte_count++] = val5b; // 高3位自动为0
    }
    *out_len = byte_count;
}

void decode_bmc(uint8_t *intervals, size_t len) {
    uint8_t bits[1024] = {0};
    int bit_index = 0;
    size_t i = 0;

    while (i < len) {
        uint8_t t = intervals[i];

        if (t == 0) {
            i++;
            continue; // 跳过异常0值
        }

        if (t >= BIT_TIME_MIN && t <= BIT_TIME_MAX) {
            // 单边沿 => bit 0
            bits[bit_index++] = 0;
            i++;
        } else if (t >= HALF_BIT_MIN && t <= HALF_BIT_MAX) {
            // 两次半bit = bit 1
            if (i + 1 < len && intervals[i + 1] >= HALF_BIT_MIN && intervals[i + 1] <= HALF_BIT_MAX) {
                bits[bit_index++] = 1;
                i += 2;
            } else {
                // 异常：只有一个half-bit
                printf("Error: unexpected single half-bit at index %d \r\n", i);
                i++;
            }
        } else {
            printf("Error: unknown interval value %d at index %d \r\n", t, i);
            i++;
        }

        // 防止越界
        if (bit_index >= sizeof(bits)) {
            printf("Error: bits buffer overflow!\r\n");
            break;
        }
    }


    /* check training for receiver */
    int rv = is_training_code(bits, 64);
    if(rv == 1)
    {
        if (bit_index < 64) {
            printf("Error: bit stream too short, bit_index=%d\r\n", bit_index);
            return;
        }
        
        uint16_t ana_len = bit_index - 64;
        
        memmove(bits, bits + 64, ana_len);
    
        uint8_t packed_bytes[512] = {0};
        int packed_len = 0;
        pack_5bit_to_byte(bits, ana_len, packed_bytes, &packed_len);
    
        winusb_send_data_ep1(packed_bytes, packed_len);

//        for(uint16_t i = 0; i < packed_len; i++)
//        {
//            printf("%02x ", packed_bytes[i]);
//        }
//        printf("\r\n");
    }
    else
    {
        printf("No training code detected.\r\n");
    }
}

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

static void pack_5bit_to_byte(const uint8_t *bit_stream, int bit_len, uint8_t *out_bytes, int *out_len) {
    int byte_count = 0;
    for (int i = 0; i + 4 < bit_len; i += 5) {
        uint8_t byte = 0;
        for (int j = 0; j < 5; j++) {
            byte |= (bit_stream[i + j] & 1) << j;  // LSB first
        }
        out_bytes[byte_count++] = byte;
    }
    *out_len = byte_count;
}

void decode_bmc(uint8_t *intervals, size_t len) {
    uint8_t bits[1024] = {0};
    int bit_index = 0;
    size_t i = 0;

    while (i < len) {
        uint8_t t = intervals[i];

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
                printf("Error: unexpected single half-bit at index %lu \r\n", i);
                i++;
            }
        } else {
            printf("Error: unknown interval value %d at index %lu \r\n", t, i);
            i++;
        }
    }

    /* check training for receiver */
    int rv = is_training_code(bits, 64);
    if(rv == 1)
    {
        memmove(bits, bits + 64, bit_index - 64);
        
        uint8_t packed_bytes[512] = {0};
        int packed_len = 0;
        pack_5bit_to_byte(bits, bit_index - 64, packed_bytes, &packed_len);

        // 发送到USB CDC
        //usbd_cdc_write(packed_bytes, packed_len);
    }
    else
    {
        printf("No training code detected.\n");
    }
}

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define BIT_TIME_MIN 0x40  // full bit 最小时间
#define BIT_TIME_MAX 0x46  // full bit 最大时间
#define HALF_BIT_MIN 0x1C  // half bit 最小时间
#define HALF_BIT_MAX 0x25  // half bit 最大时间

void decode_bmc(uint8_t *intervals, size_t len);

void bits_to_bytes(uint8_t *bits, int bit_count, uint8_t *bytes_out, int *byte_count_out);

extern int usbd_cdc_write(const uint8_t *data, uint32_t data_len);
extern int usbd_winusb_write(const uint8_t *data, uint32_t data_len);



#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define BIT_TIME_MIN  60
#define BIT_TIME_MAX  75
#define HALF_BIT_MIN  28
#define HALF_BIT_MAX  37

void decode_bmc(uint8_t index, uint8_t *intervals, size_t len);

void bits_to_bytes(uint8_t *bits, int bit_count, uint8_t *bytes_out, int *byte_count_out);

extern int winusb_send_data_ep1(const uint8_t *data, uint32_t len);
extern int winusb_send_data_ep2(const uint8_t *data, uint32_t len);
//extern int usbd_cdc_write(const uint8_t *data, uint32_t data_len);
//extern int usbd_winusb_write(const uint8_t *data, uint32_t data_len);



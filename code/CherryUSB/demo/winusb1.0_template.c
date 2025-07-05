/*
 * Copyright (c) 2024, sakumisu
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "usbd_core.h"
#include "usbd_cdc_acm.h"

#define WCID_VENDOR_CODE 0x17

#define DOUBLE_WINUSB 1

__ALIGN_BEGIN const uint8_t WCID_StringDescriptor_MSOS[18] __ALIGN_END = {
    ///////////////////////////////////////
    /// MS OS string descriptor
    ///////////////////////////////////////
    0x12,                       /* bLength */
    USB_DESCRIPTOR_TYPE_STRING, /* bDescriptorType */
    /* MSFT100 */
    'M', 0x00, 'S', 0x00, 'F', 0x00, 'T', 0x00, /* wcChar_7 */
    '1', 0x00, '0', 0x00, '0', 0x00,            /* wcChar_7 */
    WCID_VENDOR_CODE,                           /* bVendorCode */
    0x00,                                       /* bReserved */
};

#if DOUBLE_WINUSB == 0
__ALIGN_BEGIN const uint8_t WINUSB_WCIDDescriptor[40] __ALIGN_END = {
    ///////////////////////////////////////
    /// WCID descriptor
    ///////////////////////////////////////
    0x28, 0x00, 0x00, 0x00,                   /* dwLength */
    0x00, 0x01,                               /* bcdVersion */
    0x04, 0x00,                               /* wIndex */
    0x01,                                     /* bCount */
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, /* bReserved_7 */

    ///////////////////////////////////////
    /// WCID function descriptor
    ///////////////////////////////////////
    0x00, /* bFirstInterfaceNumber */
    0x01, /* bReserved */
    /* WINUSB */
    'W', 'I', 'N', 'U', 'S', 'B', 0x00, 0x00, /* cCID_8 */
    /*  */
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, /* cSubCID_8 */
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00,             /* bReserved_6 */
};
#else
__ALIGN_BEGIN const uint8_t WINUSB_WCIDDescriptor[64] __ALIGN_END = {
    ///////////////////////////////////////
    /// WCID descriptor
    ///////////////////////////////////////
    0x40, 0x00, 0x00, 0x00,                   /* dwLength */
    0x00, 0x01,                               /* bcdVersion */
    0x04, 0x00,                               /* wIndex */
    0x02,                                     /* bCount */
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, /* bReserved_7 */

    ///////////////////////////////////////
    /// WCID function descriptor
    ///////////////////////////////////////
    0x00, /* bFirstInterfaceNumber */
    0x01, /* bReserved */
    /* WINUSB */
    'W', 'I', 'N', 'U', 'S', 'B', 0x00, 0x00, /* cCID_8 */
    /*  */
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, /* cSubCID_8 */
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00,             /* bReserved_6 */

    ///////////////////////////////////////
    /// WCID function descriptor
    ///////////////////////////////////////
    0x01, /* bFirstInterfaceNumber */
    0x01, /* bReserved */
    /* WINUSB */
    'W', 'I', 'N', 'U', 'S', 'B', 0x00, 0x00, /* cCID_8 */
    /*  */
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, /* cSubCID_8 */
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00,             /* bReserved_6 */
};
#endif
__ALIGN_BEGIN const uint8_t WINUSB_IF0_WCIDProperties [142] __ALIGN_END = {
  ///////////////////////////////////////
  /// WCID property descriptor
  ///////////////////////////////////////
  0x8e, 0x00, 0x00, 0x00,                           /* dwLength */
  0x00, 0x01,                                       /* bcdVersion */
  0x05, 0x00,                                       /* wIndex */
  0x01, 0x00,                                       /* wCount */

  ///////////////////////////////////////
  /// registry propter descriptor
  ///////////////////////////////////////
  0x84, 0x00, 0x00, 0x00,                           /* dwSize */
  0x01, 0x00, 0x00, 0x00,                           /* dwPropertyDataType */
  0x28, 0x00,                                       /* wPropertyNameLength */
  /* DeviceInterfaceGUID */
  'D', 0x00, 'e', 0x00, 'v', 0x00, 'i', 0x00,       /* wcName_20 */
  'c', 0x00, 'e', 0x00, 'I', 0x00, 'n', 0x00,       /* wcName_20 */
  't', 0x00, 'e', 0x00, 'r', 0x00, 'f', 0x00,       /* wcName_20 */
  'a', 0x00, 'c', 0x00, 'e', 0x00, 'G', 0x00,       /* wcName_20 */
  'U', 0x00, 'I', 0x00, 'D', 0x00, 0x00, 0x00,      /* wcName_20 */
  0x4e, 0x00, 0x00, 0x00,                           /* dwPropertyDataLength */
  /* {1D4B2365-4749-48EA-B38A-7C6FDDDD7E26} */
  '{', 0x00, '1', 0x00, 'D', 0x00, '4', 0x00,       /* wcData_39 */
  'B', 0x00, '2', 0x00, '3', 0x00, '6', 0x00,       /* wcData_39 */
  '5', 0x00, '-', 0x00, '4', 0x00, '7', 0x00,       /* wcData_39 */
  '4', 0x00, '9', 0x00, '-', 0x00, '4', 0x00,       /* wcData_39 */
  '8', 0x00, 'E', 0x00, 'A', 0x00, '-', 0x00,       /* wcData_39 */
  'B', 0x00, '3', 0x00, '8', 0x00, 'A', 0x00,       /* wcData_39 */
  '-', 0x00, '7', 0x00, 'C', 0x00, '6', 0x00,       /* wcData_39 */
  'F', 0x00, 'D', 0x00, 'D', 0x00, 'D', 0x00,       /* wcData_39 */
  'D', 0x00, '7', 0x00, 'E', 0x00, '2', 0x00,       /* wcData_39 */
  '6', 0x00, '}', 0x00, 0x00, 0x00,                 /* wcData_39 */
};
#define  WINUSB_IF1_WCID_PROPERTIES_SIZE  (142)
__ALIGN_BEGIN const uint8_t WINUSB_IF1_WCIDProperties [142] __ALIGN_END = {
  ///////////////////////////////////////
  /// WCID property descriptor
  ///////////////////////////////////////
  0x8e, 0x00, 0x00, 0x00,                           /* dwLength */
  0x00, 0x01,                                       /* bcdVersion */
  0x05, 0x00,                                       /* wIndex */
  0x01, 0x00,                                       /* wCount */

  ///////////////////////////////////////
  /// registry propter descriptor
  ///////////////////////////////////////
  0x84, 0x00, 0x00, 0x00,                           /* dwSize */
  0x01, 0x00, 0x00, 0x00,                           /* dwPropertyDataType */
  0x28, 0x00,                                       /* wPropertyNameLength */
  /* DeviceInterfaceGUID */
  'D', 0x00, 'e', 0x00, 'v', 0x00, 'i', 0x00,       /* wcName_20 */
  'c', 0x00, 'e', 0x00, 'I', 0x00, 'n', 0x00,       /* wcName_20 */
  't', 0x00, 'e', 0x00, 'r', 0x00, 'f', 0x00,       /* wcName_20 */
  'a', 0x00, 'c', 0x00, 'e', 0x00, 'G', 0x00,       /* wcName_20 */
  'U', 0x00, 'I', 0x00, 'D', 0x00, 0x00, 0x00,      /* wcName_20 */
  0x4e, 0x00, 0x00, 0x00,                           /* dwPropertyDataLength */
  /* {1D4B2365-4749-48EA-B38A-7C6FDDDD7E26} */
  '{', 0x00, '1', 0x00, 'D', 0x00, '4', 0x00,       /* wcData_39 */
  'B', 0x00, '2', 0x00, '3', 0x00, '6', 0x00,       /* wcData_39 */
  '5', 0x00, '-', 0x00, '4', 0x00, '7', 0x00,       /* wcData_39 */
  '4', 0x00, '9', 0x00, '-', 0x00, '4', 0x00,       /* wcData_39 */
  '8', 0x00, 'E', 0x00, 'A', 0x00, '-', 0x00,       /* wcData_39 */
  'B', 0x00, '3', 0x00, '8', 0x00, 'A', 0x00,       /* wcData_39 */
  '-', 0x00, '7', 0x00, 'C', 0x00, '6', 0x00,       /* wcData_39 */
  'F', 0x00, 'D', 0x00, 'D', 0x00, 'D', 0x00,       /* wcData_39 */
  'D', 0x00, '7', 0x00, 'E', 0x00, '2', 0x00,       /* wcData_39 */
  '6', 0x00, '}', 0x00, 0x00, 0x00,                 /* wcData_39 */
};

const uint8_t *WINUSB_IFx_WCIDProperties[] = {
    WINUSB_IF0_WCIDProperties,
#if DOUBLE_WINUSB == 1
    WINUSB_IF1_WCIDProperties,
#endif
};

struct usb_msosv1_descriptor msosv1_desc = {
    .string = WCID_StringDescriptor_MSOS,
    .vendor_code = WCID_VENDOR_CODE,
    .compat_id = WINUSB_WCIDDescriptor,
    .comp_id_property = WINUSB_IFx_WCIDProperties,
};

#define WINUSB_IN_EP  0x81
#define WINUSB_OUT_EP 0x02

#define USBD_VID           0x1514
#define USBD_PID           0x1000
#define USBD_MAX_POWER     100
#define USBD_LANGID_STRING 1033

#if DOUBLE_WINUSB == 0
#define USB_CONFIG_SIZE (9 + 9 + 7 + 7)
#define INTF_NUM 1
#else
#define WINUSB_IN_EP2  0x83
#define WINUSB_OUT_EP2 0x04

#define USB_CONFIG_SIZE (9 + 9 + 7 + 7 + 9 + 7 + 7)
#define INTF_NUM 2
#endif

#ifdef CONFIG_USB_HS
#define WINUSB_EP_MPS 512
#else
#define WINUSB_EP_MPS 64
#endif

#ifdef CONFIG_USBDEV_ADVANCE_DESC
static const uint8_t device_descriptor[] = {
    USB_DEVICE_DESCRIPTOR_INIT(USB_2_0, 0x00, 0x00, 0x00, USBD_VID, USBD_PID, 0x0001, 0x01)
};

static const uint8_t config_descriptor[] = {
    USB_CONFIG_DESCRIPTOR_INIT(USB_CONFIG_SIZE, INTF_NUM, 0x01, USB_CONFIG_BUS_POWERED, USBD_MAX_POWER),
    USB_INTERFACE_DESCRIPTOR_INIT(0x00, 0x00, 0x02, 0xff, 0xff, 0x00, 0x04),
    USB_ENDPOINT_DESCRIPTOR_INIT(WINUSB_IN_EP, 0x02, WINUSB_EP_MPS, 0x00),
    USB_ENDPOINT_DESCRIPTOR_INIT(WINUSB_OUT_EP, 0x02, WINUSB_EP_MPS, 0x00),
#if DOUBLE_WINUSB == 1
    USB_INTERFACE_DESCRIPTOR_INIT(0x01, 0x00, 0x02, 0xff, 0xff, 0x00, 0x05),
    USB_ENDPOINT_DESCRIPTOR_INIT(WINUSB_IN_EP2, 0x02, WINUSB_EP_MPS, 0x00),
    USB_ENDPOINT_DESCRIPTOR_INIT(WINUSB_OUT_EP2, 0x02, WINUSB_EP_MPS, 0x00),
#endif
};

static const uint8_t device_quality_descriptor[] = {
    ///////////////////////////////////////
    /// device qualifier descriptor
    ///////////////////////////////////////
    0x0a,
    USB_DESCRIPTOR_TYPE_DEVICE_QUALIFIER,
    0x00,
    0x02,
    0x00,
    0x00,
    0x00,
    0x40,
    0x00,
    0x00,
};

static const char *string_descriptors[] = {
    (const char[]){ 0x09, 0x04 },   /* Langid */
    "GGber",                        /* Manufacturer */
    "PD SNIFFER",                   /* Product */
    "2025070524",                   /* Serial Number */
    "PD DATA",                      /* string1 */
    "ADC",                          /* string2 */
};

static const uint8_t *device_descriptor_callback(uint8_t speed)
{
    return device_descriptor;
}

static const uint8_t *config_descriptor_callback(uint8_t speed)
{
    return config_descriptor;
}

static const uint8_t *device_quality_descriptor_callback(uint8_t speed)
{
    return device_quality_descriptor;
}

static const char *string_descriptor_callback(uint8_t speed, uint8_t index)
{
    if (index > 5) {
        return NULL;
    }
    return string_descriptors[index];
}

const struct usb_descriptor winusb_descriptor = {
    .device_descriptor_callback = device_descriptor_callback,
    .config_descriptor_callback = config_descriptor_callback,
    .device_quality_descriptor_callback = device_quality_descriptor_callback,
    .string_descriptor_callback = string_descriptor_callback,
    .msosv1_descriptor = &msosv1_desc
};
#else
const uint8_t winusb_descriptor[] = {
    USB_DEVICE_DESCRIPTOR_INIT(USB_2_0, 0x00, 0x00, 0x00, USBD_VID, USBD_PID, 0x0001, 0x01),
    USB_CONFIG_DESCRIPTOR_INIT(USB_CONFIG_SIZE, INTF_NUM, 0x01, USB_CONFIG_BUS_POWERED, USBD_MAX_POWER),
    USB_INTERFACE_DESCRIPTOR_INIT(0x00, 0x00, 0x02, 0xff, 0xff, 0x00, 0x04),
    USB_ENDPOINT_DESCRIPTOR_INIT(WINUSB_IN_EP, 0x02, WINUSB_EP_MPS, 0x00),
    USB_ENDPOINT_DESCRIPTOR_INIT(WINUSB_OUT_EP, 0x02, WINUSB_EP_MPS, 0x00),
#if DOUBLE_WINUSB == 1
    USB_INTERFACE_DESCRIPTOR_INIT(0x01, 0x00, 0x02, 0xff, 0xff, 0x00, 0x05),
    USB_ENDPOINT_DESCRIPTOR_INIT(WINUSB_IN_EP2, 0x02, WINUSB_EP_MPS, 0x00),
    USB_ENDPOINT_DESCRIPTOR_INIT(WINUSB_OUT_EP2, 0x02, WINUSB_EP_MPS, 0x00),
#endif
    ///////////////////////////////////////
    /// string0 descriptor
    ///////////////////////////////////////
    USB_LANGID_INIT(USBD_LANGID_STRING),
    ///////////////////////////////////////
    /// string1 descriptor
    ///////////////////////////////////////
    0x14,                       /* bLength */
    USB_DESCRIPTOR_TYPE_STRING, /* bDescriptorType */
    'C', 0x00,                  /* wcChar0 */
    'h', 0x00,                  /* wcChar1 */
    'e', 0x00,                  /* wcChar2 */
    'r', 0x00,                  /* wcChar3 */
    'r', 0x00,                  /* wcChar4 */
    'y', 0x00,                  /* wcChar5 */
    'U', 0x00,                  /* wcChar6 */
    'S', 0x00,                  /* wcChar7 */
    'B', 0x00,                  /* wcChar8 */
    ///////////////////////////////////////
    /// string2 descriptor
    ///////////////////////////////////////
    0x2C,                       /* bLength */
    USB_DESCRIPTOR_TYPE_STRING, /* bDescriptorType */
    'C', 0x00,                  /* wcChar0 */
    'h', 0x00,                  /* wcChar1 */
    'e', 0x00,                  /* wcChar2 */
    'r', 0x00,                  /* wcChar3 */
    'r', 0x00,                  /* wcChar4 */
    'y', 0x00,                  /* wcChar5 */
    'U', 0x00,                  /* wcChar6 */
    'S', 0x00,                  /* wcChar7 */
    'B', 0x00,                  /* wcChar8 */
    ' ', 0x00,                  /* wcChar9 */
    'W', 0x00,                  /* wcChar10 */
    'I', 0x00,                  /* wcChar11 */
    'N', 0x00,                  /* wcChar12 */
    'U', 0x00,                  /* wcChar13 */
    'S', 0x00,                  /* wcChar14 */
    'B', 0x00,                  /* wcChar15 */
    ' ', 0x00,                  /* wcChar16 */
    'D', 0x00,                  /* wcChar17 */
    'E', 0x00,                  /* wcChar18 */
    'M', 0x00,                  /* wcChar19 */
    'O', 0x00,                  /* wcChar20 */
    ///////////////////////////////////////
    /// string3 descriptor
    ///////////////////////////////////////
    0x16,                       /* bLength */
    USB_DESCRIPTOR_TYPE_STRING, /* bDescriptorType */
    '2', 0x00,                  /* wcChar0 */
    '0', 0x00,                  /* wcChar1 */
    '2', 0x00,                  /* wcChar2 */
    '1', 0x00,                  /* wcChar3 */
    '1', 0x00,                  /* wcChar4 */
    '2', 0x00,                  /* wcChar5 */
    '3', 0x00,                  /* wcChar6 */
    '4', 0x00,                  /* wcChar7 */
    '5', 0x00,                  /* wcChar8 */
    '6', 0x00,                  /* wcChar9 */
    ///////////////////////////////////////
    /// string4 descriptor
    ///////////////////////////////////////
    0x30,                       /* bLength */
    USB_DESCRIPTOR_TYPE_STRING, /* bDescriptorType */
    'C', 0x00,                  /* wcChar0 */
    'h', 0x00,                  /* wcChar1 */
    'e', 0x00,                  /* wcChar2 */
    'r', 0x00,                  /* wcChar3 */
    'r', 0x00,                  /* wcChar4 */
    'y', 0x00,                  /* wcChar5 */
    'U', 0x00,                  /* wcChar6 */
    'S', 0x00,                  /* wcChar7 */
    'B', 0x00,                  /* wcChar8 */
    ' ', 0x00,                  /* wcChar9 */
    'W', 0x00,                  /* wcChar10 */
    'I', 0x00,                  /* wcChar11 */
    'N', 0x00,                  /* wcChar12 */
    'U', 0x00,                  /* wcChar13 */
    'S', 0x00,                  /* wcChar14 */
    'B', 0x00,                  /* wcChar15 */
    ' ', 0x00,                  /* wcChar16 */
    'D', 0x00,                  /* wcChar17 */
    'E', 0x00,                  /* wcChar18 */
    'M', 0x00,                  /* wcChar19 */
    'O', 0x00,                  /* wcChar20 */
    ' ', 0x00,                  /* wcChar16 */
    '1', 0x00,                  /* wcChar21 */
    ///////////////////////////////////////
    /// string5 descriptor
    ///////////////////////////////////////
    0x30,                       /* bLength */
    USB_DESCRIPTOR_TYPE_STRING, /* bDescriptorType */
    'C', 0x00,                  /* wcChar0 */
    'h', 0x00,                  /* wcChar1 */
    'e', 0x00,                  /* wcChar2 */
    'r', 0x00,                  /* wcChar3 */
    'r', 0x00,                  /* wcChar4 */
    'y', 0x00,                  /* wcChar5 */
    'U', 0x00,                  /* wcChar6 */
    'S', 0x00,                  /* wcChar7 */
    'B', 0x00,                  /* wcChar8 */
    ' ', 0x00,                  /* wcChar9 */
    'W', 0x00,                  /* wcChar10 */
    'I', 0x00,                  /* wcChar11 */
    'N', 0x00,                  /* wcChar12 */
    'U', 0x00,                  /* wcChar13 */
    'S', 0x00,                  /* wcChar14 */
    'B', 0x00,                  /* wcChar15 */
    ' ', 0x00,                  /* wcChar16 */
    'D', 0x00,                  /* wcChar17 */
    'E', 0x00,                  /* wcChar18 */
    'M', 0x00,                  /* wcChar19 */
    'O', 0x00,                  /* wcChar20 */
    ' ', 0x00,                  /* wcChar16 */
    '2', 0x00,                  /* wcChar21 */
#ifdef CONFIG_USB_HS
    ///////////////////////////////////////
    /// device qualifier descriptor
    ///////////////////////////////////////
    0x0a,
    USB_DESCRIPTOR_TYPE_DEVICE_QUALIFIER,
    0x00,
    0x02,
    0x00,
    0x00,
    0x00,
    0x40,
    0x00,
    0x00,
#endif
    0x00
};
#endif

USB_NOCACHE_RAM_SECTION USB_MEM_ALIGNX uint8_t read_buffer[2048];
USB_NOCACHE_RAM_SECTION USB_MEM_ALIGNX uint8_t write_buffer[2048];

// 数据队列结构体
#define MAX_QUEUE_SIZE 4
#define MAX_DATA_SIZE 2048

typedef struct {
    uint8_t data[MAX_DATA_SIZE];
    uint32_t length;
    bool valid;
} queue_item_t;

typedef struct {
    queue_item_t items[MAX_QUEUE_SIZE];
    uint8_t head;
    uint8_t tail;
    uint8_t count;
    bool sending;
} data_queue_t;

// 为两个端点分别创建队列
static data_queue_t ep1_queue = {0};
static data_queue_t ep2_queue = {0};

// 队列操作函数
static bool queue_is_empty(data_queue_t *queue) {
    return queue->count == 0;
}

static bool queue_is_full(data_queue_t *queue) {
    return queue->count >= MAX_QUEUE_SIZE;
}

static bool queue_enqueue(data_queue_t *queue, const uint8_t *data, uint32_t length) {
    if (queue_is_full(queue) || length > MAX_DATA_SIZE) {
        return false;
    }
    
    queue_item_t *item = &queue->items[queue->tail];
    memcpy(item->data, data, length);
    item->length = length;
    item->valid = true;
    
    queue->tail = (queue->tail + 1) % MAX_QUEUE_SIZE;
    queue->count++;
    
    return true;
}

static bool queue_dequeue(data_queue_t *queue, uint8_t *data, uint32_t *length) {
    if (queue_is_empty(queue)) {
        return false;
    }
    
    queue_item_t *item = &queue->items[queue->head];
    memcpy(data, item->data, item->length);
    *length = item->length;
    item->valid = false;
    
    queue->head = (queue->head + 1) % MAX_QUEUE_SIZE;
    queue->count--;
    
    return true;
}

static void queue_clear(data_queue_t *queue) {
    queue->head = 0;
    queue->tail = 0;
    queue->count = 0;
    queue->sending = false;
    for (int i = 0; i < MAX_QUEUE_SIZE; i++) {
        queue->items[i].valid = false;
    }
}

volatile bool ep_tx_busy_flag = false;

static void usbd_event_handler(uint8_t busid, uint8_t event)
{
    switch (event) {
        case USBD_EVENT_RESET:
            break;
        case USBD_EVENT_CONNECTED:
            break;
        case USBD_EVENT_DISCONNECTED:
            break;
        case USBD_EVENT_RESUME:
            break;
        case USBD_EVENT_SUSPEND:
            break;
        case USBD_EVENT_CONFIGURED:
            ep_tx_busy_flag = false;
            /* 初始化队列 */
            queue_clear(&ep1_queue);
#if DOUBLE_WINUSB == 1
            queue_clear(&ep2_queue);
#endif
            /* setup first out ep read transfer */
            usbd_ep_start_read(busid, WINUSB_OUT_EP, read_buffer, 2048);
#if DOUBLE_WINUSB == 1
            usbd_ep_start_read(busid, WINUSB_OUT_EP2, read_buffer, 2048);
#endif
            break;
        case USBD_EVENT_SET_REMOTE_WAKEUP:
            break;
        case USBD_EVENT_CLR_REMOTE_WAKEUP:
            break;

        default:
            break;
    }
}

void usbd_winusb_out(uint8_t busid, uint8_t ep, uint32_t nbytes)
{
//    USB_LOG_RAW("actual1 out len:%d\r\n", (unsigned int)nbytes);
//    for (int i = 0; i < nbytes; i++) {
//        printf("%02x ", read_buffer[i]);
//    }
//    printf("\r\n");
    
    // 使用独立的缓冲区避免冲突
    memcpy(write_buffer, read_buffer, nbytes);
    
    int ret = usbd_ep_start_write(busid, WINUSB_IN_EP, write_buffer, nbytes);
    
    /* setup next out ep read transfer */
    usbd_ep_start_read(busid, WINUSB_OUT_EP, read_buffer, 2048);
}

void usbd_winusb_in(uint8_t busid, uint8_t ep, uint32_t nbytes)
{
    //    USB_LOG_RAW("actual1 in len:%d\r\n", (unsigned int)nbytes);

    if ((nbytes % WINUSB_EP_MPS) == 0 && nbytes) {
        /* send zlp */
        usbd_ep_start_write(busid, WINUSB_IN_EP, NULL, 0);
    } else {
        // 传输完成，处理队列中的下一个数据
        ep1_queue.sending = false;
        
        // 检查队列中是否还有数据需要发送
        uint8_t send_data[MAX_DATA_SIZE];
        uint32_t send_length;
        
        if (queue_dequeue(&ep1_queue, send_data, &send_length)) {
            // 还有数据，继续发送
            ep1_queue.sending = true;
            memcpy(write_buffer, send_data, send_length);
            usbd_ep_start_write(busid, WINUSB_IN_EP, write_buffer, send_length);
        }
    }
}

struct usbd_endpoint winusb_out_ep1 = {
    .ep_addr = WINUSB_OUT_EP,
    .ep_cb = usbd_winusb_out
};

struct usbd_endpoint winusb_in_ep1 = {
    .ep_addr = WINUSB_IN_EP,
    .ep_cb = usbd_winusb_in
};

struct usbd_interface intf0;

#if DOUBLE_WINUSB == 1

void usbd_winusb_out2(uint8_t busid, uint8_t ep, uint32_t nbytes)
{
//    USB_LOG_RAW("actual2 out len:%d\r\n", (unsigned int)nbytes);
//    for (int i = 0; i < nbytes; i++) {
//        printf("%02x ", read_buffer[i]);
//    }
//    printf("\r\n");
    usbd_ep_start_write(busid, WINUSB_IN_EP2, read_buffer, nbytes);
    /* setup next out ep read transfer */
    usbd_ep_start_read(busid, WINUSB_OUT_EP2, read_buffer, 2048);
}

void usbd_winusb_in2(uint8_t busid, uint8_t ep, uint32_t nbytes)
{
    //    USB_LOG_RAW("actual2 in len:%d\r\n", (unsigned int)nbytes);

    if ((nbytes % usbd_get_ep_mps(busid, ep)) == 0 && nbytes) {
        /* send zlp */
        usbd_ep_start_write(busid, WINUSB_IN_EP2, NULL, 0);
    } else {
        // 传输完成，处理队列中的下一个数据
        ep2_queue.sending = false;
        
        // 检查队列中是否还有数据需要发送
        uint8_t send_data[MAX_DATA_SIZE];
        uint32_t send_length;
        
        if (queue_dequeue(&ep2_queue, send_data, &send_length)) {
            // 还有数据，继续发送
            ep2_queue.sending = true;
            memcpy(write_buffer, send_data, send_length);
            usbd_ep_start_write(busid, WINUSB_IN_EP2, write_buffer, send_length);
        }
    }
}

struct usbd_endpoint winusb_out_ep2 = {
    .ep_addr = WINUSB_OUT_EP2,
    .ep_cb = usbd_winusb_out2
};

struct usbd_endpoint winusb_in_ep2 = {
    .ep_addr = WINUSB_IN_EP2,
    .ep_cb = usbd_winusb_in2
};

struct usbd_interface intf1;

#endif

void winusb_init(uint8_t busid, uintptr_t reg_base)
{
#ifdef CONFIG_USBDEV_ADVANCE_DESC
    usbd_desc_register(busid, &winusb_descriptor);
#else
    usbd_desc_register(busid, winusb_descriptor);
#endif
#ifndef CONFIG_USBDEV_ADVANCE_DESC
    usbd_msosv1_desc_register(busid, &msosv1_desc);
#endif
    usbd_add_interface(busid, &intf0);
    usbd_add_endpoint(busid, &winusb_out_ep1);
    usbd_add_endpoint(busid, &winusb_in_ep1);
#if DOUBLE_WINUSB == 1
    usbd_add_interface(busid, &intf1);
    usbd_add_endpoint(busid, &winusb_out_ep2);
    usbd_add_endpoint(busid, &winusb_in_ep2);
#endif
    usbd_initialize(busid, reg_base, usbd_event_handler);
}

// 发送数据到第一个 WinUSB 接口 IN 端点
int winusb_send_data_ep1(const uint8_t *data, uint32_t len)
{
    if (len > MAX_DATA_SIZE) {
        // 数据太大，无法处理
        return -2;
    }
    
    // 尝试将数据加入队列
    if (!queue_enqueue(&ep1_queue, data, len)) {
        // 队列满了，无法添加新数据
        return -1;
    }
    
    // 如果当前没有在发送数据，尝试开始发送
    if (!ep1_queue.sending) {
        uint8_t send_data[MAX_DATA_SIZE];
        uint32_t send_length;
        
        if (queue_dequeue(&ep1_queue, send_data, &send_length)) {
            ep1_queue.sending = true;
            memcpy(write_buffer, send_data, send_length);
            int ret = usbd_ep_start_write(0, WINUSB_IN_EP, write_buffer, send_length);
            if (ret != 0) {
                // 发送失败，恢复队列状态
                ep1_queue.sending = false;
                // 将数据重新放回队列头部（这里简化处理，实际应该放回原位置）
                queue_enqueue(&ep1_queue, send_data, send_length);
                return -3;
            }
        }
    }
    
    return 0; // 成功加入队列
}

// 发送数据到第二个 WinUSB 接口 IN 端点（需要定义 DOUBLE_WINUSB）
int winusb_send_data_ep2(const uint8_t *data, uint32_t len)
{
#if DOUBLE_WINUSB == 1
    if (len > MAX_DATA_SIZE) {
        // 数据太大，无法处理
        return -2;
    }
    
    // 尝试将数据加入队列
    if (!queue_enqueue(&ep2_queue, data, len)) {
        // 队列满了，无法添加新数据
        return -1;
    }
    
    // 如果当前没有在发送数据，尝试开始发送
    if (!ep2_queue.sending) {
        uint8_t send_data[MAX_DATA_SIZE];
        uint32_t send_length;
        
        if (queue_dequeue(&ep2_queue, send_data, &send_length)) {
            ep2_queue.sending = true;
            memcpy(write_buffer, send_data, send_length);
            int ret = usbd_ep_start_write(0, WINUSB_IN_EP2, write_buffer, send_length);
            if (ret != 0) {
                // 发送失败，恢复队列状态
                ep2_queue.sending = false;
                // 将数据重新放回队列头部（这里简化处理，实际应该放回原位置）
                queue_enqueue(&ep2_queue, send_data, send_length);
                return -3;
            }
        }
    }
    
    return 0; // 成功加入队列
#else
    (void)data;
    (void)len;
    // 未定义双接口时返回错误
    return -3;
#endif
}

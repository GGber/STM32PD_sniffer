/*
 * Copyright (c) 2022 HPMicro
 *
 * SPDX-License-Identifier: BSD-3-Clause
 *
 */

#include "usbd_core.h"
#include "usbd_hid.h"


/*!< hidraw in endpoint */
#define HIDRAW_IN1_EP       0x81
#define HIDRAW_IN2_EP      0x83
#define HIDRAW_IN_EP_SIZE  64
#define HIDRAW_IN_INTERVAL 10

/*!< hidraw out endpoint */
#define HIDRAW_OUT1_EP          0x02
#define HIDRAW_OUT2_EP         0x04
#define HIDRAW_OUT_EP_SIZE     64
#define HIDRAW_OUT_EP_INTERVAL 10

#define USBD_VID           0x1514
#define USBD_PID           0x1000
#define USBD_MAX_POWER     100
#define USBD_LANGID_STRING 1033

/*!< config descriptor size */
#define USB_HID_CONFIG_DESC_SIZ (9 + 9 + 9 + 7 + 7 + 9 + 9 + 7 + 7)

/*!< custom hid report descriptor size */
#define HID_CUSTOM_REPORT_DESC_SIZE 38

#ifdef CONFIG_USBDEV_ADVANCE_DESC
static const uint8_t device_descriptor[] = {
    USB_DEVICE_DESCRIPTOR_INIT(USB_2_0, 0x00, 0x00, 0x00, USBD_VID, USBD_PID, 0x0002, 0x01)
};

static const uint8_t config_descriptor[] = {
    USB_CONFIG_DESCRIPTOR_INIT(USB_HID_CONFIG_DESC_SIZ, 0x02, 0x01, USB_CONFIG_BUS_POWERED, USBD_MAX_POWER),
    /************** Descriptor of Custom interface *****************/
    0x09,                          /* bLength: Interface Descriptor size */
    USB_DESCRIPTOR_TYPE_INTERFACE, /* bDescriptorType: Interface descriptor type */
    0x00,                          /* bInterfaceNumber: Number of Interface */
    0x00,                          /* bAlternateSetting: Alternate setting */
    0x02,                          /* bNumEndpoints */
    0x03,                          /* bInterfaceClass: HID */
    0x01,                          /* bInterfaceSubClass : 1=BOOT, 0=no boot */
    0x00,                          /* nInterfaceProtocol : 0=none, 1=keyboard, 2=mouse */
    0,                             /* iInterface: Index of string descriptor */
    /******************** Descriptor of Custom HID ********************/
    0x09,                    /* bLength: HID Descriptor size */
    HID_DESCRIPTOR_TYPE_HID, /* bDescriptorType: HID */
    0x11,                    /* bcdHID: HID Class Spec release number */
    0x01,
    0x00,                        /* bCountryCode: Hardware target country */
    0x01,                        /* bNumDescriptors: Number of HID class descriptors to follow */
    0x22,                        /* bDescriptorType */
    HID_CUSTOM_REPORT_DESC_SIZE, /* wItemLength: Total length of Report descriptor */
    0x00,
    /******************** Descriptor of Custom in endpoint ********************/
    0x07,                         /* bLength: Endpoint Descriptor size */
    USB_DESCRIPTOR_TYPE_ENDPOINT, /* bDescriptorType: */
    HIDRAW_IN1_EP,                 /* bEndpointAddress: Endpoint Address (IN) */
    0x03,                         /* bmAttributes: Interrupt endpoint */
    WBVAL(HIDRAW_IN_EP_SIZE),     /* wMaxPacketSize: 4 Byte max */
    HIDRAW_IN_INTERVAL,           /* bInterval: Polling Interval */
    /******************** Descriptor of Custom out endpoint ********************/
    0x07,                         /* bLength: Endpoint Descriptor size */
    USB_DESCRIPTOR_TYPE_ENDPOINT, /* bDescriptorType: */
    HIDRAW_OUT1_EP,                /* bEndpointAddress: Endpoint Address (IN) */
    0x03,                         /* bmAttributes: Interrupt endpoint */
    WBVAL(HIDRAW_OUT_EP_SIZE),    /* wMaxPacketSize: 4 Byte max */
    HIDRAW_OUT_EP_INTERVAL,       /* bInterval: Polling Interval */
    /* HID 2 */
    /************** Descriptor of Custom interface *****************/
    0x09,                          /* bLength: Interface Descriptor size */
    USB_DESCRIPTOR_TYPE_INTERFACE, /* bDescriptorType: Interface descriptor type */
    0x01,                          /* bInterfaceNumber: Number of Interface */
    0x00,                          /* bAlternateSetting: Alternate setting */
    0x02,                          /* bNumEndpoints */
    0x03,                          /* bInterfaceClass: HID */
    0x01,                          /* bInterfaceSubClass : 1=BOOT, 0=no boot */
    0x00,                          /* nInterfaceProtocol : 0=none, 1=keyboard, 2=mouse */
    0,                             /* iInterface: Index of string descriptor */
    /******************** Descriptor of Custom HID ********************/
    0x09,                    /* bLength: HID Descriptor size */
    HID_DESCRIPTOR_TYPE_HID, /* bDescriptorType: HID */
    0x11,                    /* bcdHID: HID Class Spec release number */
    0x01,
    0x00,                        /* bCountryCode: Hardware target country */
    0x01,                        /* bNumDescriptors: Number of HID class descriptors to follow */
    0x22,                        /* bDescriptorType */
    HID_CUSTOM_REPORT_DESC_SIZE, /* wItemLength: Total length of Report descriptor */
    0x00,
    /******************** Descriptor of Custom in endpoint ********************/
    0x07,                         /* bLength: Endpoint Descriptor size */
    USB_DESCRIPTOR_TYPE_ENDPOINT, /* bDescriptorType: */
    HIDRAW_IN2_EP,                 /* bEndpointAddress: Endpoint Address (IN) */
    0x03,                         /* bmAttributes: Interrupt endpoint */
    WBVAL(HIDRAW_IN_EP_SIZE),     /* wMaxPacketSize: 4 Byte max */
    HIDRAW_IN_INTERVAL,           /* bInterval: Polling Interval */
    /******************** Descriptor of Custom out endpoint ********************/
    0x07,                         /* bLength: Endpoint Descriptor size */
    USB_DESCRIPTOR_TYPE_ENDPOINT, /* bDescriptorType: */
    HIDRAW_OUT2_EP,               /* bEndpointAddress: Endpoint Address (IN) */
    0x03,                         /* bmAttributes: Interrupt endpoint */
    WBVAL(HIDRAW_OUT_EP_SIZE),    /* wMaxPacketSize: 4 Byte max */
    HIDRAW_OUT_EP_INTERVAL,       /* bInterval: Polling Interval */
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
    "PD SNIIFER",                   /* Product */
    "2025070223",                   /* Serial Number */
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
    if (index > 3) {
        return NULL;
    }
    return string_descriptors[index];
}

const struct usb_descriptor hid_descriptor = {
    .device_descriptor_callback = device_descriptor_callback,
    .config_descriptor_callback = config_descriptor_callback,
    .device_quality_descriptor_callback = device_quality_descriptor_callback,
    .string_descriptor_callback = string_descriptor_callback
};
#else
/*!< global descriptor */
static const uint8_t hid_descriptor[] = {
    USB_DEVICE_DESCRIPTOR_INIT(USB_2_0, 0x00, 0x00, 0x00, USBD_VID, USBD_PID, 0x0002, 0x01),
    USB_CONFIG_DESCRIPTOR_INIT(USB_HID_CONFIG_DESC_SIZ, 0x01, 0x01, USB_CONFIG_BUS_POWERED, USBD_MAX_POWER),
    /************** Descriptor of Custom interface *****************/
    0x09,                          /* bLength: Interface Descriptor size */
    USB_DESCRIPTOR_TYPE_INTERFACE, /* bDescriptorType: Interface descriptor type */
    0x00,                          /* bInterfaceNumber: Number of Interface */
    0x00,                          /* bAlternateSetting: Alternate setting */
    0x02,                          /* bNumEndpoints */
    0x03,                          /* bInterfaceClass: HID */
    0x01,                          /* bInterfaceSubClass : 1=BOOT, 0=no boot */
    0x00,                          /* nInterfaceProtocol : 0=none, 1=keyboard, 2=mouse */
    0,                             /* iInterface: Index of string descriptor */
    /******************** Descriptor of Custom HID ********************/
    0x09,                    /* bLength: HID Descriptor size */
    HID_DESCRIPTOR_TYPE_HID, /* bDescriptorType: HID */
    0x11,                    /* bcdHID: HID Class Spec release number */
    0x01,
    0x00,                        /* bCountryCode: Hardware target country */
    0x01,                        /* bNumDescriptors: Number of HID class descriptors to follow */
    0x22,                        /* bDescriptorType */
    HID_CUSTOM_REPORT_DESC_SIZE, /* wItemLength: Total length of Report descriptor */
    0x00,
    /******************** Descriptor of Custom in endpoint ********************/
    0x07,                         /* bLength: Endpoint Descriptor size */
    USB_DESCRIPTOR_TYPE_ENDPOINT, /* bDescriptorType: */
    HIDRAW_IN_EP,                 /* bEndpointAddress: Endpoint Address (IN) */
    0x03,                         /* bmAttributes: Interrupt endpoint */
    WBVAL(HIDRAW_IN_EP_SIZE),     /* wMaxPacketSize: 4 Byte max */
    HIDRAW_IN_INTERVAL,           /* bInterval: Polling Interval */
    /******************** Descriptor of Custom out endpoint ********************/
    0x07,                         /* bLength: Endpoint Descriptor size */
    USB_DESCRIPTOR_TYPE_ENDPOINT, /* bDescriptorType: */
    HIDRAW_OUT_EP,                /* bEndpointAddress: Endpoint Address (IN) */
    0x03,                         /* bmAttributes: Interrupt endpoint */
    WBVAL(HIDRAW_OUT_EP_SIZE),    /* wMaxPacketSize: 4 Byte max */
    HIDRAW_OUT_EP_INTERVAL,       /* bInterval: Polling Interval */
    /* 73 */
    /*
     * string0 descriptor
     */
    USB_LANGID_INIT(USBD_LANGID_STRING),
    /*
     * string1 descriptor
     */
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
    /*
     * string2 descriptor
     */
    0x26,                       /* bLength */
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
    'H', 0x00,                  /* wcChar10 */
    'I', 0x00,                  /* wcChar11 */
    'D', 0x00,                  /* wcChar12 */
    ' ', 0x00,                  /* wcChar13 */
    'D', 0x00,                  /* wcChar14 */
    'E', 0x00,                  /* wcChar15 */
    'M', 0x00,                  /* wcChar16 */
    'O', 0x00,                  /* wcChar17 */
    /*
     * string3 descriptor
     */
    0x16,                       /* bLength */
    USB_DESCRIPTOR_TYPE_STRING, /* bDescriptorType */
    '2', 0x00,                  /* wcChar0 */
    '0', 0x00,                  /* wcChar1 */
    '2', 0x00,                  /* wcChar2 */
    '2', 0x00,                  /* wcChar3 */
    '1', 0x00,                  /* wcChar4 */
    '2', 0x00,                  /* wcChar5 */
    '3', 0x00,                  /* wcChar6 */
    '4', 0x00,                  /* wcChar7 */
    '5', 0x00,                  /* wcChar8 */
    '6', 0x00,                  /* wcChar9 */
#ifdef CONFIG_USB_HS
    /*
     * device qualifier descriptor
     */
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

/*!< custom hid report descriptor */
static const uint8_t hid_custom_report_desc1[HID_CUSTOM_REPORT_DESC_SIZE] = {
    /* USER CODE BEGIN 0 */
    0x06, 0x00, 0xff, /* USAGE_PAGE (Vendor Defined Page 1) */
    0x09, 0x01,       /* USAGE (Vendor Usage 1) */
    0xa1, 0x01,       /* COLLECTION (Application) */
    0x85, 0x02,       /*   REPORT ID (0x02) */
    0x09, 0x01,       /*   USAGE (Vendor Usage 1) */
    0x15, 0x00,       /*   LOGICAL_MINIMUM (0) */
    0x26, 0xff, 0x00, /*   LOGICAL_MAXIMUM (255) */
    0x95, 0x40 - 1,   /*   REPORT_COUNT (63) */
    0x75, 0x08,       /*   REPORT_SIZE (8) */
    0x81, 0x02,       /*   INPUT (Data,Var,Abs) */
    /* <___________________________________________________> */
    0x85, 0x01,       /*   REPORT ID (0x01) */
    0x09, 0x01,       /*   USAGE (Vendor Usage 1) */
    0x15, 0x00,       /*   LOGICAL_MINIMUM (0) */
    0x26, 0xff, 0x00, /*   LOGICAL_MAXIMUM (255) */
    0x95, 0x40 - 1,   /*   REPORT_COUNT (63) */
    0x75, 0x08,       /*   REPORT_SIZE (8) */
    0x91, 0x02,       /*   OUTPUT (Data,Var,Abs) */
    /* USER CODE END 0 */
    0xC0 /*     END_COLLECTION	             */
};

static const uint8_t hid_custom_report_desc2[HID_CUSTOM_REPORT_DESC_SIZE] = {
    /* USER CODE BEGIN 0 */
    0x06, 0x00, 0xff, /* USAGE_PAGE (Vendor Defined Page 1) */
    0x09, 0x01,       /* USAGE (Vendor Usage 1) */
    0xa1, 0x01,       /* COLLECTION (Application) */
    0x85, 0x04,       /*   REPORT ID (0x04) */
    0x09, 0x01,       /*   USAGE (Vendor Usage 1) */
    0x15, 0x00,       /*   LOGICAL_MINIMUM (0) */
    0x26, 0xff, 0x00, /*   LOGICAL_MAXIMUM (255) */
    0x95, 0x40 - 1,   /*   REPORT_COUNT (63) */
    0x75, 0x08,       /*   REPORT_SIZE (8) */
    0x81, 0x02,       /*   INPUT (Data,Var,Abs) */
    /* <___________________________________________________> */
    0x85, 0x03,       /*   REPORT ID (0x03) */
    0x09, 0x01,       /*   USAGE (Vendor Usage 1) */
    0x15, 0x00,       /*   LOGICAL_MINIMUM (0) */
    0x26, 0xff, 0x00, /*   LOGICAL_MAXIMUM (255) */
    0x95, 0x40 - 1,   /*   REPORT_COUNT (63) */
    0x75, 0x08,       /*   REPORT_SIZE (8) */
    0x91, 0x02,       /*   OUTPUT (Data,Var,Abs) */
    /* USER CODE END 0 */
    0xC0 /*     END_COLLECTION	             */
};

USB_NOCACHE_RAM_SECTION USB_MEM_ALIGNX uint8_t read1_buffer[HIDRAW_OUT_EP_SIZE];
USB_NOCACHE_RAM_SECTION USB_MEM_ALIGNX uint8_t send1_buffer[HIDRAW_IN_EP_SIZE];
USB_NOCACHE_RAM_SECTION USB_MEM_ALIGNX uint8_t read2_buffer[HIDRAW_OUT_EP_SIZE];
USB_NOCACHE_RAM_SECTION USB_MEM_ALIGNX uint8_t send2_buffer[HIDRAW_IN_EP_SIZE];

#define HID_STATE_IDLE 0
#define HID_STATE_BUSY 1

/*!< hid state ! Data can be sent only when state is idle  */
static volatile uint8_t custom1_state;
static volatile uint8_t custom2_state;

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
        /* setup first out ep read transfer */
        usbd_ep_start_read(busid, HIDRAW_OUT1_EP, read1_buffer, HIDRAW_OUT_EP_SIZE);
        usbd_ep_start_read(busid, HIDRAW_OUT2_EP, read2_buffer, HIDRAW_OUT_EP_SIZE);
        break;
    case USBD_EVENT_SET_REMOTE_WAKEUP:
        break;
    case USBD_EVENT_CLR_REMOTE_WAKEUP:
        break;

    default:
        break;
    }
}

static void usbd_hid1_custom_in_callback(uint8_t busid, uint8_t ep, uint32_t nbytes)
{
    (void)busid;
    (void)ep;
    USB_LOG_RAW("actual1 in len:%d\r\n", (unsigned int)nbytes);
    custom1_state = HID_STATE_IDLE;
}

static void usbd_hid1_custom_out_callback(uint8_t busid, uint8_t ep, uint32_t nbytes)
{
    USB_LOG_RAW("actual1 out len:%d\r\n", (unsigned int)nbytes);
    
    //handle receive buffer
    
    usbd_ep_start_write(busid, HIDRAW_IN1_EP, read1_buffer, nbytes);
}

static void usbd_hid2_custom_in_callback(uint8_t busid, uint8_t ep, uint32_t nbytes)
{
    (void)busid;
    (void)ep;
    USB_LOG_RAW("actual2 in len:%d\r\n", (unsigned int)nbytes);
    custom2_state = HID_STATE_IDLE;
}

static void usbd_hid2_custom_out_callback(uint8_t busid, uint8_t ep, uint32_t nbytes)
{
    USB_LOG_RAW("actual2 out len:%d\r\n", (unsigned int)nbytes);

    //handle receive buffer
    
    usbd_ep_start_write(busid, HIDRAW_IN2_EP, read2_buffer, nbytes);
}

static struct usbd_endpoint custom1_in_ep = {
    .ep_cb = usbd_hid1_custom_in_callback,
    .ep_addr = HIDRAW_IN1_EP
};

static struct usbd_endpoint custom1_out_ep = {
    .ep_cb = usbd_hid1_custom_out_callback,
    .ep_addr = HIDRAW_OUT1_EP
};

static struct usbd_endpoint custom2_in_ep = {
    .ep_cb = usbd_hid2_custom_in_callback,
    .ep_addr = HIDRAW_IN2_EP
};

static struct usbd_endpoint custom2_out_ep = {
    .ep_cb = usbd_hid2_custom_out_callback,
    .ep_addr = HIDRAW_OUT2_EP
};

/* function ------------------------------------------------------------------*/
/**
 * @brief            hid custom init
 * @pre              none
 * @param[in]        none
 * @retval           none
 */
struct usbd_interface intf0;
struct usbd_interface intf1;

void hid_custom_init(uint8_t busid, uintptr_t reg_base)
{
#ifdef CONFIG_USBDEV_ADVANCE_DESC
    usbd_desc_register(busid, &hid_descriptor);
#else
    usbd_desc_register(busid, hid_descriptor);
#endif
    usbd_add_interface(busid, usbd_hid_init_intf(busid, &intf0, hid_custom_report_desc1, HID_CUSTOM_REPORT_DESC_SIZE));
    usbd_add_endpoint(busid, &custom1_in_ep);
    usbd_add_endpoint(busid, &custom1_out_ep);

    usbd_add_interface(busid, usbd_hid_init_intf(busid, &intf1, hid_custom_report_desc2, HID_CUSTOM_REPORT_DESC_SIZE));
    usbd_add_endpoint(busid, &custom2_in_ep);
    usbd_add_endpoint(busid, &custom2_out_ep);
    
    usbd_initialize(busid, reg_base, usbd_event_handler);
}


// 发送状态
static volatile uint8_t custom_state1 = HID_STATE_IDLE;
static volatile uint8_t custom_state2 = HID_STATE_IDLE;

// 内部函数：独立 buffer 支持
static int hid_send_internal(uint8_t busid, uint8_t ep, uint8_t report_id,
                             const uint8_t *src, uint32_t length,
                             uint8_t *send_buffer, volatile uint8_t *state)
{
    if (length > (HIDRAW_IN_EP_SIZE - 1)) {
        return -1; // 超出最大
    }

    if (*state != HID_STATE_IDLE) {
        return -1; // 正在发送
    }

    send_buffer[0] = report_id;
    memcpy(&send_buffer[1], src, length);

    *state = HID_STATE_BUSY;
    return usbd_ep_start_write(busid, ep, send_buffer, length + 1);
}

// 接口 1 发送
int hid_send_to_if1(const uint8_t *data, uint32_t length)
{
    return hid_send_internal(0, HIDRAW_IN1_EP, 0x02, data, length, send1_buffer, &custom_state1);
}

// 接口 2 发送
int hid_send_to_if2(const uint8_t *data, uint32_t length)
{
    return hid_send_internal(0, HIDRAW_IN2_EP, 0x04, data, length, send2_buffer, &custom_state2);
}

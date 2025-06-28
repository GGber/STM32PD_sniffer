/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * File Name          : app_freertos.c
  * Description        : Code for freertos applications
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "FreeRTOS.h"
#include "task.h"
#include "main.h"
#include "cmsis_os.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "usart.h"
#include "adc.h"
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

#define CC_DEBOUNCE_ATTACH_TIME 100 // Debounce time in milliseconds
#define CC_DEBOUNCE_DETACH_TIME 10  // Debounce time in milliseconds
#define CC_MAX_ADC_VALUE 2200 // Maximum ADC value for CC detection 
#define CC_MIN_ADC_VALUE 300 // Minimum ADC value for CC detection

enum cc_state{
    CC_IDLE,
    CC_ATTACH_WAIT,
    CC_ATTACH,
    CC_DETACH_WAIT,
    CC_DETACH,
} ;

typedef struct {
  uint8_t flag_cc_attach;
  uint16_t adc_cc; // ADC value for CC1
  uint32_t cc_debounce_time;
  enum cc_state state;
} cc_detect_t;

cc_detect_t cc_detect[2];
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN Variables */

/* USER CODE END Variables */
/* Definitions for LedTask */
osThreadId_t LedTaskHandle;
const osThreadAttr_t LedTask_attributes = {
  .name = "LedTask",
  .priority = (osPriority_t) osPriorityNormal,
  .stack_size = 128 * 4
};
/* Definitions for PDTask */
osThreadId_t PDTaskHandle;
const osThreadAttr_t PDTask_attributes = {
  .name = "PDTask",
  .priority = (osPriority_t) osPriorityAboveNormal,
  .stack_size = 1024 * 4
};
/* Definitions for TimeIndexQueue */
osMessageQueueId_t TimeIndexQueueHandle;
const osMessageQueueAttr_t TimeIndexQueue_attributes = {
  .name = "TimeIndexQueue"
};

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */

/* USER CODE END FunctionPrototypes */

void StartLedTask(void *argument);
void StartTaskPD(void *argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/**
  * @brief  FreeRTOS initialization
  * @param  None
  * @retval None
  */
void MX_FREERTOS_Init(void) {
  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* Create the queue(s) */
  /* creation of TimeIndexQueue */
  TimeIndexQueueHandle = osMessageQueueNew (8, sizeof(uint8_t), &TimeIndexQueue_attributes);

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */

  /* Create the thread(s) */
  /* creation of LedTask */
  LedTaskHandle = osThreadNew(StartLedTask, NULL, &LedTask_attributes);

  /* creation of PDTask */
  PDTaskHandle = osThreadNew(StartTaskPD, NULL, &PDTask_attributes);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

  /* USER CODE BEGIN RTOS_EVENTS */
  /* add events, ... */
  /* USER CODE END RTOS_EVENTS */

}

/* USER CODE BEGIN Header_StartLedTask */
/**
  * @brief  Function implementing the LedTask thread.
  * @param  argument: Not used
  * @retval None
  */
/* USER CODE END Header_StartLedTask */
void StartLedTask(void *argument)
{
  /* USER CODE BEGIN StartLedTask */
  /* Infinite loop */
  for(;;)
  {
    HAL_GPIO_WritePin(GPIOB, LED1_Pin, GPIO_PIN_RESET);
    osDelay(500); // Delay for 500 ms
    HAL_GPIO_WritePin(GPIOB, LED1_Pin, GPIO_PIN_SET);
    osDelay(500); // Delay for 500 ms
  }
  /* USER CODE END StartLedTask */
}

/* USER CODE BEGIN Header_StartTaskPD */
/**
* @brief Function implementing the PDTask thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartTaskPD */
void StartTaskPD(void *argument)
{
  /* USER CODE BEGIN StartTaskPD */

  memset(cc_detect, 0, sizeof(cc_detect));

  /* Infinite loop */
  for(;;)
  {
    cc_detect[0].adc_cc = adc_cc1 * 3000 / 4096; // Convert ADC value to mV
    cc_detect[1].adc_cc = adc_cc2 * 3000 / 4096; // Convert ADC value to mV
    //printf("CC1 ADC: %d mV, CC2 ADC: %d mV\r\n", cc_detect[0].adc_cc, cc_detect[1].adc_cc);

    for(uint8_t index = 0; index < 2; index++){

      switch(cc_detect[index].state)
      {
        case CC_IDLE:
        {
          cc_detect[index].flag_cc_attach = 0;
          if ((cc_detect[index].adc_cc <= CC_MAX_ADC_VALUE) && (cc_detect[index].adc_cc >= CC_MIN_ADC_VALUE)) {
            cc_detect[index].state = CC_ATTACH_WAIT;
            cc_detect[index].cc_debounce_time = osKernelGetTickCount();
          }
          break;
        }

        case CC_ATTACH_WAIT:
        {
          if ((cc_detect[index].adc_cc < CC_MIN_ADC_VALUE) || (cc_detect[index].adc_cc > CC_MAX_ADC_VALUE)) {
            cc_detect[index].state = CC_IDLE; // Back to idle if ADC is above threshold
          } else if ((osKernelGetTickCount() - cc_detect[index].cc_debounce_time) >= CC_DEBOUNCE_ATTACH_TIME) {
            cc_detect[index].flag_cc_attach = 1; // Set attach flag
            cc_detect[index].state = CC_ATTACH; // Transition to attach state after debounce
            printf("CC%d Attach Detected\r\n", index + 1);
          }
          break;
        }

        case CC_ATTACH:
        {
          if ((cc_detect[index].adc_cc < CC_MIN_ADC_VALUE) || (cc_detect[index].adc_cc > CC_MAX_ADC_VALUE)) {
            cc_detect[index].state = CC_DETACH_WAIT; // Transition to detach wait state
            cc_detect[index].cc_debounce_time = osKernelGetTickCount();
          }
          break;
        }

        case  CC_DETACH_WAIT:
        {
          if ((cc_detect[index].adc_cc <= CC_MAX_ADC_VALUE) && (cc_detect[index].adc_cc >= CC_MIN_ADC_VALUE)) {
            cc_detect[index].state = CC_ATTACH; // Back to attach state if ADC is above threshold
          } else if ((osKernelGetTickCount() - cc_detect[index].cc_debounce_time) >= CC_DEBOUNCE_DETACH_TIME) {
            cc_detect[index].state = CC_DETACH; // Transition to detach state after debounce
            printf("CC%d Detach Detected\r\n", index + 1);
          }
          break;
        }

        case CC_DETACH:
        {
          cc_detect[index].state = CC_IDLE; // Back to idle if ADC is below threshold
          break;
        }

        default:
        {
          cc_detect[index].state = CC_IDLE; // Reset to idle state if an unknown state is encountered
          break;
        }
      }
    }

    osDelay(500);
  }
  /* USER CODE END StartTaskPD */
}

/* Private application code --------------------------------------------------*/
/* USER CODE BEGIN Application */

/* USER CODE END Application */


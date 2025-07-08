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
#include <string.h>
#include "usart.h"
#include "adc.h"
#include "comp.h"
#include "tim.h"
#include "bmc_analyze.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
#define CC_DEBOUNCE_ATTACH_TIME 100 // Debounce time in milliseconds
#define CC_DEBOUNCE_DETACH_TIME 10  // Debounce time in milliseconds
#define CC_MAX_ADC_VALUE 2500 // Maximum ADC value for CC detection 
#define CC_MIN_ADC_VALUE 500  // Minimum ADC value for CC detection

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
  .stack_size = 4096 * 4
};
/* Definitions for CCTask */
osThreadId_t CCTaskHandle;
const osThreadAttr_t CCTask_attributes = {
  .name = "CCTask",
  .priority = (osPriority_t) osPriorityAboveNormal1,
  .stack_size = 256 * 4
};
/* Definitions for TimeIndexQueue */
osMessageQueueId_t TimeIndexQueueHandle;
const osMessageQueueAttr_t TimeIndexQueue_attributes = {
  .name = "TimeIndexQueue"
};

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN FunctionPrototypes */
void handle_cc_attach(void);
void handle_cc_detach(void);
/* USER CODE END FunctionPrototypes */

void StartLedTask(void *argument);
void StartTaskPD(void *argument);
void StartTaskCC(void *argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/* Hook prototypes */
void vApplicationStackOverflowHook(xTaskHandle xTask, signed char *pcTaskName);
void vApplicationMallocFailedHook(void);

/* USER CODE BEGIN 4 */
void vApplicationStackOverflowHook(xTaskHandle xTask, signed char *pcTaskName)
{
   /* Run time stack overflow checking is performed if
   configCHECK_FOR_STACK_OVERFLOW is defined to 1 or 2. This hook function is
   called if a stack overflow is detected. */
    
    printf(" Stack overflow detected in task: %s\r\n", pcTaskName);

    TaskStatus_t taskList[10];
    UBaseType_t taskCount = uxTaskGetSystemState(taskList, 10, NULL);

    for (int i = 0; i < taskCount; i++) {
        printf("Task: %s | Stack Free: %u\r\n",
               taskList[i].pcTaskName,
               taskList[i].usStackHighWaterMark);
    }

    taskDISABLE_INTERRUPTS();
    for(;;);
}
/* USER CODE END 4 */

/* USER CODE BEGIN 5 */
void vApplicationMallocFailedHook(void)
{
   /* vApplicationMallocFailedHook() will only be called if
   configUSE_MALLOC_FAILED_HOOK is set to 1 in FreeRTOSConfig.h. It is a hook
   function that will get called if a call to pvPortMalloc() fails.
   pvPortMalloc() is called internally by the kernel whenever a task, queue,
   timer or semaphore is created. It is also called by various parts of the
   demo application. If heap_1.c or heap_2.c are used, then the size of the
   heap available to pvPortMalloc() is defined by configTOTAL_HEAP_SIZE in
   FreeRTOSConfig.h, and the xPortGetFreeHeapSize() API function can be used
   to query the size of free heap space that remains (although it does not
   provide information on how the remaining heap might be fragmented). */
}
/* USER CODE END 5 */

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

  /* creation of CCTask */
  CCTaskHandle = osThreadNew(StartTaskCC, NULL, &CCTask_attributes);

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
    extern int usbd_cdc_write(const uint8_t *data, uint32_t data_len);
  /* Infinite loop */
  for(;;)
  {
    HAL_GPIO_WritePin(GPIOB, LED1_Pin, GPIO_PIN_RESET);
    osDelay(500); // Delay for 500 ms
    HAL_GPIO_WritePin(GPIOB, LED1_Pin, GPIO_PIN_SET);
    osDelay(500); // Delay for 500 ms
      
    TaskStatus_t taskList[10];
    UBaseType_t taskCount = uxTaskGetSystemState(taskList, 10, NULL);

//    for (int i = 0; i < taskCount; i++) {
//        printf("Task: %s | Stack Free: %u\r\n",
//               taskList[i].pcTaskName,
//               taskList[i].usStackHighWaterMark);
//    }
//    printf("\r\n");
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

  uint8_t buffer_index;
  /* Infinite loop */
  for(;;)
  {
    osMessageQueueGet(TimeIndexQueueHandle, &buffer_index, NULL, portMAX_DELAY);

    uint8_t data_time[MAX_BUFFER_LEN];
    /* last data is invalid */
    uint16_t data_time_len = time2_data_len[buffer_index] - 2;
    if(data_time_len <= MAX_BUFFER_LEN)
    {
      memcpy(data_time, &time2_data_buffer[buffer_index][1], data_time_len);
      decode_bmc(buffer_index, data_time, data_time_len);
    }
    


    // printf("\r\n");
    // for(uint16_t i = 0; i < data_time_len; i++)
    // {
    //   printf("%d ", data_time[i]);
    // }
    // printf("\r\n");
    

  }
  /* USER CODE END StartTaskPD */
}

/* USER CODE BEGIN Header_StartTaskCC */
/**
* @brief Function implementing the CCTask thread.
* @param argument: Not used
* @retval None
*/
/* USER CODE END Header_StartTaskCC */
void StartTaskCC(void *argument)
{
  /* USER CODE BEGIN StartTaskCC */
  memset(cc_detect, 0, sizeof(cc_detect));
    
  /* Infinite loop */
  for(;;)
  {
    cc_detect[0].adc_cc = adc1_value * 2 * 3300 / 4096; // Convert ADC value to mV
    cc_detect[1].adc_cc = adc2_value * 2 * 3300 / 4096; // Convert ADC value to mV

    //printf(" %d  %d \r\n", cc_detect[0].adc_cc, cc_detect[1].adc_cc);
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
            handle_cc_attach();
            cc_detect[index].state = CC_ATTACH; // Transition to attach state after debounce
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
            cc_detect[index].flag_cc_attach = 0; // Set attach flag
            handle_cc_detach();
            cc_detect[index].state = CC_DETACH; // Transition to detach state after debounce
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

    osDelay(5);
  }
  /* USER CODE END StartTaskCC */
}

/* Private application code --------------------------------------------------*/
/* USER CODE BEGIN Application */

void HAL_COMP_TriggerCallback(COMP_HandleTypeDef *hcomp)
{
  LL_EXTI_DisableFallingTrig_0_31(LL_EXTI_LINE_21 | LL_EXTI_LINE_22);
    
  /* open timeout event */
  __HAL_TIM_CLEAR_FLAG(&htim2, TIM_FLAG_UPDATE);
  __HAL_TIM_ENABLE_IT(&htim2,  TIM_IT_UPDATE);
}

void timer2_timeout_handle(void)
{
  /* close update interrupt */
  __HAL_TIM_DISABLE_IT(&htim2, TIM_IT_UPDATE);

  /* open cc interrupt */
  LL_EXTI_ClearFlag_0_31(LL_EXTI_LINE_21 | LL_EXTI_LINE_22);
  LL_EXTI_EnableFallingTrig_0_31(LL_EXTI_LINE_21 | LL_EXTI_LINE_22);
  
  /* data len */
  uint16_t transferred = MAX_BUFFER_LEN - __HAL_DMA_GET_COUNTER(htim2.hdma[TIM_DMA_ID_CC1]);
  time2_data_len[buffer_index] = transferred;
  time_data_systick[buffer_index] = osKernelGetTickCount();

  /* handle data */
  /* Send buffer index to message queue */
  osMessageQueuePut(TimeIndexQueueHandle, (uint8_t *)&buffer_index, 0, 0);

  /* start next buffer */
  buffer_index++;
  if(buffer_index >= MAX_BUFFER_INDEX)
  {
    buffer_index = 0;
  }
  
  HAL_TIM_IC_Stop_DMA(&htim2, TIM_CHANNEL_1);
  /* start DMA channel */
  HAL_TIM_IC_Start_DMA(&htim2, TIM_CHANNEL_1, (uint32_t*)time2_data_buffer[buffer_index], MAX_BUFFER_LEN);
}

void handle_cc_attach(void)
{
  if(cc_detect[0].flag_cc_attach == 1 && cc_detect[1].flag_cc_attach == 0)
  {
    /* change to comp1 */
    HAL_TIMEx_TISelection(&htim2, TIM_TIM2_TI1_COMP1, TIM_CHANNEL_1);

    /* open comp interrupt */
    HAL_COMP_Start(&hcomp1);
      
    LL_EXTI_ClearFlag_0_31(LL_EXTI_LINE_21 | LL_EXTI_LINE_22);
    LL_EXTI_EnableFallingTrig_0_31(LL_EXTI_LINE_21 | LL_EXTI_LINE_22);
    
    /* start DMA channel */
    HAL_TIM_IC_Start_DMA(&htim2, TIM_CHANNEL_1, (uint32_t*)time2_data_buffer[buffer_index], MAX_BUFFER_LEN);
      
//    DEBUG_PRINT("CC1 attach\r\n");
  }
  else if(cc_detect[1].flag_cc_attach == 1 && cc_detect[0].flag_cc_attach == 0)
  {
    /* change to comp2 */
    HAL_TIMEx_TISelection(&htim2, TIM_TIM2_TI1_COMP2, TIM_CHANNEL_1);

    /* open cc interrupt */
    HAL_COMP_Start(&hcomp2);
    
    LL_EXTI_ClearFlag_0_31(LL_EXTI_LINE_21 | LL_EXTI_LINE_22);
    LL_EXTI_EnableFallingTrig_0_31(LL_EXTI_LINE_21 | LL_EXTI_LINE_22);
    
    /* start DMA channel */
    HAL_TIM_IC_Start_DMA(&htim2, TIM_CHANNEL_1, (uint32_t*)time2_data_buffer[buffer_index], MAX_BUFFER_LEN);
      
//    DEBUG_PRINT("CC2 attach\r\n");
  }
}

void handle_cc_detach(void)
{
  if(cc_detect[0].flag_cc_attach == 0 && cc_detect[1].flag_cc_attach == 0)
  {
//    DEBUG_PRINT("CC1/2 detach\r\n");

    HAL_COMP_Stop(&hcomp1);
    HAL_COMP_Stop(&hcomp2);
    
    LL_EXTI_DisableFallingTrig_0_31(LL_EXTI_LINE_21 | LL_EXTI_LINE_22);
    __HAL_TIM_DISABLE_IT(&htim2, TIM_IT_UPDATE);

    HAL_TIM_IC_Stop_DMA(&htim2, TIM_CHANNEL_1);
  }
}




/* USER CODE END Application */


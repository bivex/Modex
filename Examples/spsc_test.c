/* Test driver for real open-source spsc_queue */

#include <stdint.h>
#include <string.h>

#define SPSC_QUEUE_SIZE 4
#define ELEMENT_TYPE uint32_t

#include "spscq/include/spsc_queue.h"

spsc_queue_t q;

void test_producer(void) {
    uint32_t val = 42;
    enqueue(&q, val);
}

void test_consumer(void) {
    uint32_t val = 0;
    dequeue(&q, &val);
}

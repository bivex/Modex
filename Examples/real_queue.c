/* Real-world test target: Bounded Ring Buffer Queue */

#define CAPACITY 4

int buffer[CAPACITY];
int head = 0;
int tail = 0;
int count = 0;

void push(int item) {
    if (count < CAPACITY) {
        buffer[tail] = item;
        tail = (tail + 1) % CAPACITY;
        count++;
    }
}

int pop(void) {
    int item = -1;
    if (count > 0) {
        item = buffer[head];
        head = (head + 1) % CAPACITY;
        count--;
    }
    return item;
}

void producer_consumer(void) {
    push(42);
    pop();
}

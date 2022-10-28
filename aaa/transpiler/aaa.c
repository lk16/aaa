#include <malloc.h>
#include <assert.h>

#include "aaa.h"

void aaa_stack_init(struct aaa_stack *stack) {
    stack->size = 0;
    stack->max_size = 1024;
    stack->data = malloc(1024 * sizeof(struct aaa_stack));
}

void aaa_stack_free(struct aaa_stack *stack) {
    free(stack->data);
}

void aaa_stack_push_int(struct aaa_stack *stack, int value) {
    assert(stack->size < stack->max_size);

    struct aaa_variable *top = stack->data + stack->size;
    top->kind = AAA_INTEGER;
    top->integer = value;

    stack->size++;
}

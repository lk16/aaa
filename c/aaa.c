#include "aaa.h"

#include <assert.h>
#include <stdio.h>

void aaa_stack_item_init_int(struct aaa_stack_item *item, int value) {
    item->type = AAA_INTEGER;
    item->int_value = value;
}

void aaa_stack_item_init_bool(struct aaa_stack_item *item, bool value) {
    item->type = AAA_BOOLEAN;
    item->bool_value = value;
}

void aaa_stack_item_print(const struct aaa_stack_item *item) {
    switch (item->type) {
        case AAA_INTEGER:
            printf("%d", item->int_value);
            break;
        case AAA_BOOLEAN:
            if (item->bool_value) {
                printf("%s", "true");
            } else {
                printf("%s", "false");
            }
            break;
        default:
            assert(0);
    }
}

void aaa_stack_init(struct aaa_stack *stack, size_t max_size) {
    stack->size = 0;
    stack->max_size = max_size;
    stack->items = malloc(max_size * sizeof(*stack->items));
}

void aaa_stack_destroy(struct aaa_stack *stack) {
    free(stack->items);
}

void aaa_stack_print(const struct aaa_stack *stack) {
    for (size_t i=0; i<stack->size; i++) {
        aaa_stack_item_print(stack->items + i);
        if (i != stack->size - 1) {
            printf("%s", " ");
        }
    }
    printf("\n");
}

void aaa_instruction_run(const struct aaa_instruction *instr, struct aaa_stack *stack) {
    switch (instr->type) {
        case AAA_INTEGER_PUSH:
            aaa_instruction_run_integer_push(instr, stack);
            break;
        case AAA_INTEGER_PRINT:
            aaa_instruction_run_integer_print(instr, stack);
            break;
        case AAA_INTEGER_ADD:
            aaa_instruction_run_integer_add(instr, stack);
            break;
        case AAA_NEWLINE_PRINT:
            aaa_instruction_run_newline_print(instr, stack);
            break;
        default:
            assert(0);
    }
}

void aaa_instruction_run_integer_push(const struct aaa_instruction *instr, struct aaa_stack *stack) {
    if (stack->size == stack->max_size) {
        // TODO handle stack overflow
    }

    stack->size++;
    struct aaa_stack_item *top = stack->items + stack->size - 1;
    aaa_stack_item_init_int(top, instr->integer_push_value);
}

void aaa_instruction_run_integer_print(const struct aaa_instruction *instr, struct aaa_stack *stack) {
    (void)instr;
    struct aaa_stack_item *top = stack->items + stack->size - 1;
    printf("%d", top->int_value);
    stack->size--;
}

void aaa_instruction_run_integer_add(const struct aaa_instruction *instr, struct aaa_stack *stack) {
    (void)instr;
    int sum = stack->items[stack->size - 1].int_value + stack->items[stack->size - 2].int_value;

    stack->size--;
    stack->items[stack->size - 1].int_value = sum;
}

void aaa_instruction_run_newline_print(const struct aaa_instruction *instr, struct aaa_stack *stack) {
    (void)instr;
    (void)stack;
    printf("%s", "\n");
}

const struct aaa_instruction INSTRUCTIONS[] = {
    (struct aaa_instruction){type: AAA_INTEGER_PUSH, integer_push_value: 34},
    (struct aaa_instruction){type: AAA_INTEGER_PUSH, integer_push_value: 35},
    (struct aaa_instruction){type: AAA_INTEGER_ADD},
    (struct aaa_instruction){type: AAA_INTEGER_PRINT},
    (struct aaa_instruction){type: AAA_NEWLINE_PRINT},
};

const size_t NUM_INSTRUCTIONS = 5;

int main() {
    struct aaa_stack stack;
    aaa_stack_init(&stack, 1024);

    for (size_t i=0; i<NUM_INSTRUCTIONS; i++) {
        const struct aaa_instruction *instr = INSTRUCTIONS + i;
        aaa_instruction_run(instr, &stack);
    }

    aaa_stack_destroy(&stack);
    return 0;
}

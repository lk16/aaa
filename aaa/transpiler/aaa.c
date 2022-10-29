#include <malloc.h>
#include <assert.h>
#include <stdlib.h>

#include "aaa.h"

static void aaa_variable_check_kind(struct aaa_variable *var, enum aaa_kind kind) {
    if (var->kind != kind) {
        fprintf(stderr, "Aaa type error\n");
        abort();
    }
}

void aaa_stack_init(struct aaa_stack *stack) {
    stack->size = 0;
    stack->max_size = 1024;
    stack->data = malloc(stack->max_size * sizeof(struct aaa_stack));
}

void aaa_stack_free(struct aaa_stack *stack) {
    free(stack->data);
}

static struct aaa_variable *aaa_stack_top(struct aaa_stack *stack) {
    return stack->data + stack->size - 1;
}

static struct aaa_variable *aaa_stack_push(struct aaa_stack *stack) {
    if (stack->size >= stack->max_size) {
        fprintf(stderr, "Aaa stack overflow\n");
        abort();
    }

    stack->size++;
    return aaa_stack_top(stack);
}

void aaa_stack_push_variable(struct aaa_stack *stack, struct aaa_variable *variable) {
    struct aaa_variable *top = aaa_stack_push(stack);
    *top = *variable;
}


struct aaa_variable *aaa_stack_pop(struct aaa_stack *stack) {
    if (stack->size == 0) {
        fprintf(stderr, "Aaa stack underflow\n");
        abort();
    }

    struct aaa_variable *popped = aaa_stack_top(stack);
    stack->size--;
    return popped;
}

void aaa_stack_push_int(struct aaa_stack *stack, int value) {
    struct aaa_variable *top = aaa_stack_push(stack);
    top->kind = AAA_INTEGER;
    top->integer = value;
}

void aaa_stack_push_str(struct aaa_stack *stack, const char *value) {
    struct aaa_variable *top = aaa_stack_push(stack);
    top->kind = AAA_STRING;
    top->string = value;
}

void aaa_stack_push_bool(struct aaa_stack *stack, bool value) {
    struct aaa_variable *top = aaa_stack_push(stack);
    top->kind = AAA_BOOLEAN;
    top->boolean = value;
}

bool aaa_stack_pop_bool(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    aaa_variable_check_kind(top, AAA_BOOLEAN);
    return top->boolean;
}

static int aaa_stack_pop_int(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    aaa_variable_check_kind(top, AAA_INTEGER);
    return top->integer;
}

void aaa_stack_dup(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_top(stack);
    struct aaa_variable *dupped = aaa_stack_push(stack);

    *dupped = *top;
}

void aaa_stack_plus(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_int(stack, lhs + rhs);
}

void aaa_stack_print(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);

    switch(top->kind) {
        case AAA_BOOLEAN:
            if (top->boolean) {
                printf("%s", "true");
            } else {
                printf("%s", "false");
            }
            break;
        case AAA_INTEGER:
            printf("%d", top->integer);
            break;
        case AAA_STRING:
            printf("%s", top->string);
            break;
        default:
            fprintf(stderr, "Unhandled variable kind\n");
            abort();
    }
}

void aaa_stack_drop(struct aaa_stack *stack) {
    aaa_stack_pop(stack);
}

void aaa_stack_less(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_bool(stack, lhs < rhs);
}

void aaa_stack_modulo(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);

    if (rhs == 0) {
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_bool(stack, false);
    } else {
        aaa_stack_push_int(stack, lhs % rhs);
        aaa_stack_push_bool(stack, true);
    }
}

void aaa_stack_equals(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_bool(stack, lhs == rhs);
}
void aaa_stack_or(struct aaa_stack *stack) {
    bool rhs = aaa_stack_pop_bool(stack);
    bool lhs = aaa_stack_pop_bool(stack);
    aaa_stack_push_bool(stack, lhs || rhs);
}

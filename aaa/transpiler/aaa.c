#include <malloc.h>
#include <assert.h>
#include <stdlib.h>

#include "aaa.h"

void aaa_stack_init(struct aaa_stack *stack) {
    stack->size = 0;
    stack->max_size = 1024;
    stack->data = malloc(stack->max_size * sizeof(struct aaa_stack));
}

void aaa_stack_free(struct aaa_stack *stack) {
    free(stack->data);
}

void aaa_stack_push_int(struct aaa_stack *stack, int value) {
    if (stack->size >= stack->max_size) {
        fprintf(stderr, "Aaa stack overflow\n");
        abort();
    }

    struct aaa_variable *top = stack->data + stack->size;
    top->kind = AAA_INTEGER;
    top->integer = value;

    stack->size++;
}

void aaa_stack_push_str(struct aaa_stack *stack, const char *value) {
    if (stack->size >= stack->max_size) {
        fprintf(stderr, "Aaa stack overflow\n");
        abort();
    }

    struct aaa_variable *top = stack->data + stack->size;
    top->kind = AAA_STRING;
    top->string = value;

    stack->size++;
}

bool aaa_stack_pop_bool(struct aaa_stack *stack) {
    if (stack->size == 0) {
        fprintf(stderr, "Aaa stack underflow\n");
        abort();
    }

    struct aaa_variable *top = stack->data + stack->size - 1;

    if (top->kind != AAA_BOOLEAN) {
        fprintf(stderr, "Type error\n");
        abort();
    }

    stack->size--;

    return top->boolean;
}

void aaa_stack_dup(struct aaa_stack *stack) {
    if (stack->size >= stack->max_size) {
        fprintf(stderr, "Aaa stack overflow\n");
        abort();
    }

    if (stack->size == 0) {
        fprintf(stderr, "Aaa stack underflow\n");
        abort();
    }

    stack->data[stack->size] = stack->data[stack->size - 1];
    stack->size++;
}

void aaa_stack_plus(struct aaa_stack *stack) {
    if (stack->size == 0) {
        fprintf(stderr, "Aaa stack underflow\n");
        abort();
    }

    struct aaa_variable *top = stack->data + stack->size - 1;
    struct aaa_variable *below = stack->data + stack->size - 2;

    if (top->kind != AAA_INTEGER) {
        fprintf(stderr, "Type error\n");
        abort();
    }

    if (below->kind != AAA_INTEGER) {
        fprintf(stderr, "Type error\n");
        abort();
    }

    below->integer += top->integer;
    stack->size--;
}

void aaa_stack_print(struct aaa_stack *stack) {
    if (stack->size == 0) {
        fprintf(stderr, "Aaa stack underflow\n");
        abort();
    }

    struct aaa_variable *top = stack->data + stack->size - 1;

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

    stack->size--;
}

void aaa_stack_drop(struct aaa_stack *stack) {
    stack->size--;
}

void aaa_stack_less(struct aaa_stack *stack) {
    if (stack->size == 0) {
        fprintf(stderr, "Aaa stack underflow\n");
        abort();
    }

    struct aaa_variable *top = stack->data + stack->size - 1;
    struct aaa_variable *below = stack->data + stack->size - 2;

    if (top->kind != AAA_INTEGER) {
        fprintf(stderr, "Type error\n");
        abort();
    }

    if (below->kind != AAA_INTEGER) {
        fprintf(stderr, "Type error\n");
        abort();
    }

    bool less = below->integer < top->integer;
    below->kind = AAA_BOOLEAN;
    below->boolean = less;

    stack->size--;
}

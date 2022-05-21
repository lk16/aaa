#include <stdbool.h>
#include <stdlib.h>

enum aaa_stack_item_type {
    AAA_INTEGER,
    AAA_BOOLEAN,
    // TODO more
};


struct aaa_stack_item {
    enum aaa_stack_item_type type;
    union {
        struct {
            bool bool_value;
        };
        struct {
            int int_value;
        };
        // TODO more
    };
};

void aaa_stack_item_init_int(struct aaa_stack_item *item, int value);
void aaa_stack_item_init_bool(struct aaa_stack_item *item, bool value);

void aaa_stack_item_print(const struct aaa_stack_item *item);

struct aaa_stack {
    size_t size, max_size;
    struct aaa_stack_item *items;
};

void aaa_stack_init(struct aaa_stack *stack, size_t max_size);
void aaa_stack_destroy(struct aaa_stack *stack);

void aaa_stack_print(const struct aaa_stack *stack);

enum aaa_instruction_type {
    AAA_INTEGER_PUSH,
    AAA_INTEGER_PRINT,
    AAA_INTEGER_ADD,
    AAA_NEWLINE_PRINT,
};

struct aaa_instruction {
    enum aaa_instruction_type type;
    union {
        struct {
            int integer_push_value;
        };
    };
};

void aaa_instruction_run(const struct aaa_instruction *instr, struct aaa_stack *stack);

void aaa_instruction_run_integer_push(const struct aaa_instruction *instr, struct aaa_stack *stack);
void aaa_instruction_run_integer_print(const struct aaa_instruction *instr, struct aaa_stack *stack);
void aaa_instruction_run_integer_add(const struct aaa_instruction *instr, struct aaa_stack *stack);
void aaa_instruction_run_newline_print(const struct aaa_instruction *instr, struct aaa_stack *stack);

#include "var.h"

#include <stdio.h>
#include <malloc.h>
#include <stdlib.h>
#include <string.h>

#include "buffer.h"
#include "vector.h"
#include "map.h"


char *aaa_variable_repr(const struct aaa_variable *var) {
    switch (var->kind) {
        case AAA_BOOLEAN:
            if (var->boolean) {
                return "true";
            } else {
                return "false";
            }
        case AAA_INTEGER:
            (void)0;
            size_t buff_size = snprintf(NULL, 0, "%d", var->integer);
            char *int_buff = malloc(buff_size + 1);
            snprintf(int_buff, buff_size + 1, "%d", var->integer);
            return int_buff;
        case AAA_STRING:
            (void)0;
            struct aaa_buffer buff;
            aaa_buffer_init(&buff);
            aaa_buffer_append(&buff, "\"");
            const char *c = var->string;

            while (*c) {
                switch (*c) {
                    case '\a': aaa_buffer_append(&buff, "\\a"); break;
                    case '\b': aaa_buffer_append(&buff, "\\b"); break;
                    case '\f': aaa_buffer_append(&buff, "\\f"); break;
                    case '\n': aaa_buffer_append(&buff, "\\n"); break;
                    case '\r': aaa_buffer_append(&buff, "\\r"); break;
                    case '\t': aaa_buffer_append(&buff, "\\t"); break;
                    case '\v': aaa_buffer_append(&buff, "\\v"); break;
                    case '\\': aaa_buffer_append(&buff, "\\\\"); break;
                    case '\'': aaa_buffer_append(&buff, "\\'"); break;
                    case '\"': aaa_buffer_append(&buff, "\\\""); break;
                    default:
                        (void)0;
                        char str[2] = "\0";
                        str[0] = *c;
                        aaa_buffer_append(&buff, str);
                }
                c++;
            }
            aaa_buffer_append(&buff, "\"");
            return buff.data;
        case AAA_VECTOR:
            return aaa_vec_repr(var->vector);
        case AAA_MAP:
            return aaa_map_repr(var->map);
        default:
            fprintf(stderr, "aaa_variable_repr Unhandled variable kind\n");
            abort();
    }
}

size_t aaa_variable_hash(const struct aaa_variable *var) {
    switch (var->kind) {
        case AAA_BOOLEAN:
            if (var->boolean) {
                return 1;
            } else {
                return 0;
            }
        case AAA_INTEGER:
            return (var->integer ^ 0x123456789) + (var->integer << 13) + (var->integer >> 17);
        case AAA_STRING:
            (void)0;
            size_t hash = 0;
            const char *c = var->string;
            while (*c) {
                hash = (hash * 123457) + *c;
                c++;
            }
            return hash;
        case AAA_VECTOR:
            fprintf(stderr, "Cannot hash a vector!\n");
            abort();
        default:
            fprintf(stderr, "aaa_variable_hash Unhandled variable kind\n");
            abort();
    }
}

bool aaa_variable_equals(const struct aaa_variable *lhs, const struct aaa_variable *rhs) {
    if (lhs->kind != rhs->kind) {
        return false;
    }

    switch (lhs->kind) {
        case AAA_BOOLEAN:
            return lhs->boolean == rhs->boolean;
        case AAA_INTEGER:
            return lhs->integer == rhs->integer;
        case AAA_STRING:
            return strcmp(lhs->string, rhs->string) == 0;
        case AAA_VECTOR:
            // TODO use vector equality function when present
            if (lhs->vector->size != rhs->vector->size) {
                return false;
            }
            for (size_t i=0; i<lhs->vector->size; i++) {
                struct aaa_variable *lhs_item = NULL, *rhs_item = NULL;
                aaa_vector_get(lhs->vector, i, lhs_item);
                aaa_vector_get(rhs->vector, i, rhs_item);
                if (!aaa_variable_equals(lhs_item, rhs_item)) {
                    return false;
                }
            }
            return true;
        default:
            fprintf(stderr, "aaa_variable_equals Unhandled variable kind\n");
            abort();
    }
}

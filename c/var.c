#include <stdio.h>
#include <malloc.h>
#include <stdlib.h>
#include <string.h>

#include "buffer.h"
#include "vector.h"
#include "map.h"
#include "var.h"

const char *aaa_variable_repr(const struct aaa_variable *var) {
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
            struct aaa_buffer *buff = aaa_buffer_new();
            aaa_buffer_append(buff, "\"");
            const char *c = var->string;

            while (*c) {
                switch (*c) {
                    case '\a': aaa_buffer_append(buff, "\\a"); break;
                    case '\b': aaa_buffer_append(buff, "\\b"); break;
                    case '\f': aaa_buffer_append(buff, "\\f"); break;
                    case '\n': aaa_buffer_append(buff, "\\n"); break;
                    case '\r': aaa_buffer_append(buff, "\\r"); break;
                    case '\t': aaa_buffer_append(buff, "\\t"); break;
                    case '\v': aaa_buffer_append(buff, "\\v"); break;
                    case '\\': aaa_buffer_append(buff, "\\\\"); break;
                    case '\'': aaa_buffer_append(buff, "\\'"); break;
                    case '\"': aaa_buffer_append(buff, "\\\""); break;
                    default:
                        (void)0;
                        char str[2] = "\0";
                        str[0] = *c;
                        aaa_buffer_append(buff, str);
                }
                c++;
            }
            aaa_buffer_append(buff, "\"");
            const char *repr = aaa_buffer_to_string(buff);
            aaa_buffer_dec_ref(buff);
            return repr;
        case AAA_VECTOR:
            return aaa_vector_repr(var->vector);
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
            return aaa_vector_equals(lhs->vector, rhs->vector);
        default:
            fprintf(stderr, "aaa_variable_equals Unhandled variable kind\n");
            abort();
    }
}

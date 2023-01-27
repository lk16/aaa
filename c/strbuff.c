#include <malloc.h>
#include <string.h>

#include "ref_count.h"
#include "str.h"
#include "strbuff.h"

struct aaa_string_buffer {
    struct aaa_ref_count ref_count;
    size_t max_size;
    char *data;
    size_t size;
};

struct aaa_string_buffer *aaa_string_buffer_new(void) {
    struct aaa_string_buffer *buff = malloc(sizeof(*buff));
    aaa_ref_count_init(&buff->ref_count);
    buff->max_size = 1024;
    buff->data = malloc(buff->max_size * sizeof(char));
    buff->size = 0;
    buff->data[buff->size] = '\0';
    return buff;
}

static void
aaa_string_buffer_append_sized_c_string(struct aaa_string_buffer *buff,
                                        const char *str, size_t length) {
    while (buff->size + length + 1 > buff->max_size) {
        char *new_data = malloc(2 * buff->max_size * sizeof(char));
        memcpy(new_data, buff->data, buff->max_size);
        free(buff->data);
        buff->data = new_data;
        buff->max_size *= 2;
    }

    memcpy(buff->data + buff->size, str, length);
    buff->size += length;
    buff->data[buff->size] = '\0';
}

void aaa_string_buffer_append_c_string(struct aaa_string_buffer *buff,
                                       const char *str) {
    size_t length = strlen(str);
    aaa_string_buffer_append_sized_c_string(buff, str, length);
}

void aaa_string_buffer_append_string(struct aaa_string_buffer *buff,
                                     const struct aaa_string *string) {
    size_t length = aaa_string_len(string);
    const char *c_str = aaa_string_raw(string);
    aaa_string_buffer_append_sized_c_string(buff, c_str, length);
}

struct aaa_string *aaa_string_buffer_to_string(struct aaa_string_buffer *buff) {
    char *data = buff->data;
    aaa_string_buffer_dec_ref(buff);
    return aaa_string_new(data, true);
}

void aaa_string_buffer_dec_ref(struct aaa_string_buffer *buff) {
    if (aaa_ref_count_dec(&buff->ref_count) == 0) {
        free(buff);
    }
}

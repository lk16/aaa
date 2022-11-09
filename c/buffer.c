#include <malloc.h>
#include <string.h>

#include "buffer.h"
#include "ref_count.h"

struct aaa_buffer {
    struct aaa_ref_count ref_count;
    size_t max_size;
    char *data;
    size_t size;
};

struct aaa_buffer *aaa_buffer_new(void){
    struct aaa_buffer *buff = malloc(sizeof(*buff));
    aaa_ref_count_init(&buff->ref_count);
    buff->max_size = 1024;
    buff->data = malloc(buff->max_size * sizeof(char));
    buff->size = 0;
    buff->data[buff->size] = '\0';
    return buff;
}

void aaa_buffer_append(struct aaa_buffer *buff, const char *str) {
    size_t len = strlen(str);

    while (buff->size + len + 1 > buff->max_size) {
        char *new_data = malloc(2 * buff->max_size * sizeof(char));
        memcpy(new_data, buff->data, buff->max_size);
        free(buff->data);
        buff->data = new_data;
        buff->max_size *= 2;
    }

    memcpy(buff->data + buff->size, str, len);
    buff->size += len;
    buff->data[buff->size] = '\0';
}

struct aaa_string *aaa_buffer_to_string(const struct aaa_buffer *buff) {
    return aaa_string_new(buff->data, true);
}

void aaa_buffer_dec_ref(struct aaa_buffer *buff) {
    if (aaa_ref_count_dec(&buff->ref_count) == 0) {
        free(buff);
    }
}

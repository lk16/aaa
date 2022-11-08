#include "buffer.h"

#include <malloc.h>
#include <string.h>

void aaa_buffer_init(struct aaa_buffer *buff) {
    buff->max_size = 1024;
    buff->data = malloc(buff->max_size * sizeof(char));
    buff->size = 0;
    buff->data[buff->size] = '\0';
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

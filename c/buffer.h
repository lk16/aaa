#pragma once

#include <stddef.h>

struct aaa_buffer {
    size_t max_size;
    char *data;
    size_t size;
};

void aaa_buffer_init(struct aaa_buffer *buff);
void aaa_buffer_append(struct aaa_buffer *buff, const char *str);

#pragma once

#include "types.h"

struct aaa_buffer *aaa_buffer_new(void);
void aaa_buffer_dec_ref(struct aaa_buffer *buff);

void aaa_buffer_append_c_string(struct aaa_buffer *buff, const char *str);
void aaa_buffer_append_string(struct aaa_buffer *buff,
                              const struct aaa_string *string);

struct aaa_string *aaa_buffer_to_string(struct aaa_buffer *buff);

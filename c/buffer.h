#pragma once

#include "types.h"

struct aaa_buffer *aaa_buffer_new(void);
void aaa_buffer_append(struct aaa_buffer *buff, const char *str);
struct aaa_string *aaa_buffer_to_string(const struct aaa_buffer *buff);
void aaa_buffer_dec_ref(struct aaa_buffer *buff);

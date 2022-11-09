#pragma once

#include <stdbool.h>

struct aaa_string;

struct aaa_string *aaa_string_new(const char *raw, bool freeable);
const char *aaa_string_raw(const struct aaa_string *string);
void aaa_string_dec_ref(struct aaa_string *string);

#pragma once

#include "types.h"

struct aaa_string *aaa_string_new(char *raw, bool freeable);
const char *aaa_string_raw(const struct aaa_string *string);
void aaa_string_dec_ref(struct aaa_string *string);
void aaa_string_inc_ref(struct aaa_string *string);

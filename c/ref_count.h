#pragma once

#include "types.h"

struct aaa_ref_count {
    size_t count;
};

void aaa_ref_count_init(struct aaa_ref_count *ref_count);
void aaa_ref_count_inc(struct aaa_ref_count *ref_count);
size_t aaa_ref_count_dec(struct aaa_ref_count *ref_count);

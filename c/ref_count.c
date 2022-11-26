#include "ref_count.h"

void aaa_ref_count_inc(struct aaa_ref_count *ref_count) { ref_count->count++; }

size_t aaa_ref_count_dec(struct aaa_ref_count *ref_count) {
    ref_count->count--;
    return ref_count->count;
}

void aaa_ref_count_init(struct aaa_ref_count *ref_count) {
    ref_count->count = 1;
}

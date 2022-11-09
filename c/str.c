#include <malloc.h>

#include "str.h"
#include "ref_count.h"

struct aaa_string {
    struct aaa_ref_count ref_count;
    char *raw;
    bool freeable;
};

struct aaa_string *aaa_string_new(char *raw, bool freeable) {
    struct aaa_string *string = malloc(sizeof(*string));
    aaa_ref_count_init(&string->ref_count);
    string->raw = raw;
    string->freeable = freeable;
    return string;
}

const char *aaa_string_raw(const struct aaa_string *string) {
    return string->raw;
}

void aaa_string_dec_ref(struct aaa_string *string) {
    if (aaa_ref_count_dec(&string->ref_count) == 0) {
        if (string->freeable) {
            free(string->raw);
            free(string);
        }
    }
}

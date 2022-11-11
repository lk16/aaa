#include <malloc.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>
#include <limits.h>

#include "str.h"
#include "ref_count.h"
#include "buffer.h"
#include "vector.h"

struct aaa_string {
    struct aaa_ref_count ref_count;
    char *raw;
    size_t length;
    bool freeable;
};

struct aaa_string *aaa_string_new(char *raw, bool freeable) {
    struct aaa_string *string = malloc(sizeof(*string));
    aaa_ref_count_init(&string->ref_count);
    string->raw = raw;
    string->freeable = freeable;
    string->length = strlen(raw);
    return string;
}

const char *aaa_string_raw(const struct aaa_string *string) {
    return string->raw;
}

void aaa_string_dec_ref(struct aaa_string *string) {
    if (aaa_ref_count_dec(&string->ref_count) == 0) {
        if (string->freeable) {
            free(string->raw);
        }
        free(string);
    }
}

void aaa_string_inc_ref(struct aaa_string *string) {
    aaa_ref_count_inc(&string->ref_count);
}

struct aaa_string *aaa_string_append(const struct aaa_string *string, const struct aaa_string *other) {
    char *combined = malloc((string->length + other->length + 1) *sizeof(char));
    combined[0] = '\0';
    strcat(combined, string->raw);
    strcat(combined, other->raw);
    return aaa_string_new(combined, true);
}

bool aaa_string_contains(const struct aaa_string *string, const struct aaa_string *search) {
    return strstr(string->raw, search->raw) != NULL;
}

bool aaa_string_equals(const struct aaa_string *string, const struct aaa_string *other) {
    return strcmp(string->raw, other->raw) == 0;
}

struct aaa_string *aaa_string_join(const struct aaa_string *string, struct aaa_vector *parts) {
    struct aaa_buffer *buff = aaa_buffer_new();
    struct aaa_string *part = NULL;
    struct aaa_variable *var = NULL;

    size_t part_count = aaa_vector_size(parts);

    if (part_count >= 1) {
        var = aaa_vector_get(parts, 0);
        part = aaa_variable_get_str(var);
        aaa_buffer_append(buff, part->raw);
    }

    for (size_t i=1; i<part_count; i++) {
        var = aaa_vector_get(parts, i);
        part = aaa_variable_get_str(var);

        aaa_buffer_append(buff, string->raw);
        aaa_buffer_append(buff, part->raw);
    }

    struct aaa_string *joined = aaa_buffer_to_string(buff);
    aaa_buffer_dec_ref(buff);
    return joined;
}

size_t aaa_string_len(const struct aaa_string *string) {
    return string->length;
}

struct aaa_string *aaa_string_lower(const struct aaa_string *string) {
    char *lower = malloc((string->length + 1) * sizeof(char));
    strcpy(lower, string->raw);

    char *c = lower;

    while(*c) {
        *c = tolower(*c);
        c++;
    }

    return aaa_string_new(lower, true);
}

struct aaa_string *aaa_string_upper(const struct aaa_string *string) {
    char *upper = malloc((string->length + 1) * sizeof(char));
    strcpy(upper, string->raw);

    char *c = upper;

    while(*c) {
        *c = tolower(*c);
        c++;
    }

    return aaa_string_new(upper, true);
}

void aaa_string_find(const struct aaa_string *string, const struct aaa_string *search, int *offset_out, bool *success_out) {
    aaa_string_find_after(string, search, 0, offset_out, success_out);
}

void aaa_string_find_after(const struct aaa_string *string, const struct aaa_string *search, int start, int *offset_out, bool *success_out) {
    char *location = strstr(string->raw + start, search->raw);

    if (location) {
        *offset_out = location - string->raw;
        *success_out = true;
    } else {
        *offset_out = 0;
        *success_out = false;
    }
}

void aaa_string_to_bool(const struct aaa_string *string, bool *boolean_out, bool *success_out) {
    if (strcmp("false", string->raw) == 0) {
        *boolean_out = false;
        *success_out = true;
        return;
    }

    if (strcmp("true", string->raw) == 0) {
        *boolean_out = true;
        *success_out = true;
        return;
    }

    *boolean_out = false;
    *success_out = false;
}

void aaa_string_to_int(const struct aaa_string *string, int *integer_out, bool *success_out) {
    char * end = NULL;
    long converted = strtol(string->raw, &end, 10);

    if (converted > INT_MAX || converted < INT_MIN || end == string->raw) {
        *success_out = false;
        *integer_out = 0;
    }

    *integer_out = (int)converted;
}

struct aaa_string *aaa_string_replace(const struct aaa_string *string, const struct aaa_string *search, const struct aaa_string *replace);
struct aaa_vector *aaa_string_split(const struct aaa_string *string, const struct aaa_string *sep);
struct aaa_string *aaa_string_strip(const struct aaa_string *string);
void aaa_string_substr(const struct aaa_string *string, int start, int end, bool *success_out);

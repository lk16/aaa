#pragma once

#include "types.h"

struct aaa_string *aaa_string_new(const char *raw, bool freeable);

void aaa_string_dec_ref(struct aaa_string *string);
void aaa_string_inc_ref(struct aaa_string *string);

const char *aaa_string_raw(const struct aaa_string *string);

struct aaa_string *aaa_string_append(const struct aaa_string *string,
                                     const struct aaa_string *other);
bool aaa_string_contains(const struct aaa_string *string,
                         const struct aaa_string *search);
bool aaa_string_equals(const struct aaa_string *string,
                       const struct aaa_string *other);
struct aaa_string *aaa_string_join(const struct aaa_string *string,
                                   struct aaa_vector *parts);
size_t aaa_string_len(const struct aaa_string *string);
struct aaa_string *aaa_string_lower(const struct aaa_string *string);
struct aaa_string *aaa_string_replace(const struct aaa_string *string,
                                      const struct aaa_string *search,
                                      const struct aaa_string *replace);
struct aaa_vector *aaa_string_split(const struct aaa_string *string,
                                    const struct aaa_string *sep);
struct aaa_string *aaa_string_strip(const struct aaa_string *string);
struct aaa_string *aaa_string_upper(const struct aaa_string *string);
void aaa_string_find_after(const struct aaa_string *string,
                           const struct aaa_string *search, size_t start,
                           size_t *offset_out, bool *success_out);
void aaa_string_find(const struct aaa_string *string,
                     const struct aaa_string *search, size_t *offset_out,
                     bool *success_out);
struct aaa_string *aaa_string_substr(const struct aaa_string *string,
                                     size_t start, size_t end,
                                     bool *success_out);
void aaa_string_to_bool(const struct aaa_string *string, bool *boolean_out,
                        bool *success_out);
void aaa_string_to_int(const struct aaa_string *string, int *integer_out,
                       bool *success_out);

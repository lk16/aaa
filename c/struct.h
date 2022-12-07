#pragma once

#include "types.h"

struct aaa_struct;

struct aaa_struct *aaa_struct_new(char *type_name);
void aaa_struct_dec_ref(struct aaa_struct *s);
void aaa_struct_inc_ref(struct aaa_struct *s);

// Should only be used when a struct is newly created
void aaa_struct_create_field(struct aaa_struct *s, const char *field_name,
                             struct aaa_variable *new_value);

struct aaa_variable *aaa_struct_get_field(struct aaa_struct *s,
                                          const char *field_name);
void aaa_struct_set_field(struct aaa_struct *s, const char *field_name,
                          struct aaa_variable *new_value);

struct aaa_string *aaa_struct_get_type_name(struct aaa_struct *s);

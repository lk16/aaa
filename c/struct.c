#include <stdio.h>
#include <malloc.h>
#include <stdlib.h>

#include "struct.h"
#include "map.h"
#include "ref_count.h"
#include "str.h"

struct aaa_struct {
    struct aaa_ref_count ref_count;
    struct aaa_string *type_name;
    struct aaa_map *map;
};

struct aaa_struct *aaa_struct_new(char *type_name) {
    struct aaa_struct *s = malloc(sizeof(*s));
    aaa_ref_count_init(&s->ref_count);
    s->map = aaa_map_new();
    s->type_name = aaa_string_new(type_name, false);
    return s;
}

void aaa_struct_dec_ref(struct aaa_struct *s) {
    if (aaa_ref_count_dec(&s->ref_count) == 0) {
        aaa_map_dec_ref(s->map);
        aaa_string_dec_ref(s->type_name);
        free(s);
    }
}

void aaa_struct_inc_ref(struct aaa_struct *s) {
    aaa_ref_count_inc(&s->ref_count);
}

static void aaa_struct_upsert_field(struct aaa_struct *s, char *field_name, struct aaa_variable *new_value, bool create) {
    struct aaa_string *key = aaa_string_new(field_name, false);
    struct aaa_variable *key_var = aaa_variable_new_str(key);

    bool has_key = aaa_map_has_key(s->map, key_var);

    if (has_key == create) {
        fprintf(stderr, "Struct upserting failed: create=%d, has_key=%d\n", create, has_key);
        abort();
    }

    aaa_map_set(s->map, key_var, new_value);

    aaa_variable_dec_ref(key_var);
}

void aaa_struct_create_field(struct aaa_struct *s, char *field_name, struct aaa_variable *new_value) {
    aaa_struct_upsert_field(s, field_name, new_value, true);
}

void aaa_struct_set_field(struct aaa_struct *s, char *field_name, struct aaa_variable *new_value) {
    aaa_struct_upsert_field(s, field_name, new_value, false);
}

struct aaa_variable *aaa_struct_get_field(struct aaa_struct *s, char *field_name) {
    struct aaa_string *key = aaa_string_new(field_name, false);
    struct aaa_variable *key_var = aaa_variable_new_str(key);

    struct aaa_variable *field_value = aaa_map_get(s->map, key_var);

    if (!field_value) {
        fprintf(stderr, "Struct does not have field %s\n", field_name);
        abort();
    }

    aaa_variable_dec_ref(key_var);
    return field_value;
}

struct aaa_string *aaa_struct_get_type_name(struct aaa_struct *s) {
    aaa_string_inc_ref(s->type_name);
    return s->type_name;
}

#pragma once

#include <stddef.h>

#include "aaa.h"

struct aaa_map_item {
    struct aaa_variable key, value;
    size_t hash;
    struct aaa_map_item *next;
};

struct aaa_map {
    size_t bucket_count;
    struct aaa_map_item **buckets;
    size_t size;
};

void aaa_map_init(struct aaa_map *map);
void aaa_map_free(struct aaa_map *map);

char *aaa_map_repr(const struct aaa_map *map);

void aaa_map_clear(struct aaa_map *map);
void aaa_map_copy(struct aaa_map *map, struct aaa_map *copy);
void aaa_map_drop(struct aaa_map *map, const struct aaa_variable *key);
bool aaa_map_empty(const struct aaa_map *map);
struct aaa_variable *aaa_map_get(struct aaa_map *map, const struct aaa_variable *key);
bool aaa_map_has_key(struct aaa_map *map, const struct aaa_variable *key);
struct aaa_variable *aaa_map_pop(struct aaa_map *map, const struct aaa_variable *key);
void aaa_map_set(struct aaa_map *map, const struct aaa_variable *key, const struct aaa_variable *value);
size_t aaa_map_size(const struct aaa_map *map);

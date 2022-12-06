
#include <malloc.h>
#include <stdlib.h>

#include "buffer.h"
#include "map.h"
#include "ref_count.h"
#include "str.h"
#include "var.h"

struct aaa_map_item {
    struct aaa_variable *key, *value;
    size_t hash;
    struct aaa_map_item *next;
};

struct aaa_map {
    struct aaa_ref_count ref_count;
    size_t bucket_count;
    struct aaa_map_item **buckets;
    size_t size;
};

struct aaa_map *aaa_map_new(void) {
    struct aaa_map *map = malloc(sizeof(*map));
    aaa_ref_count_init(&map->ref_count);
    map->size = 0;
    map->bucket_count = 16;
    map->buckets = malloc(map->bucket_count * sizeof(*map->buckets));
    for (size_t b = 0; b < map->bucket_count; b++) {
        map->buckets[b] = NULL;
    }
    return map;
}

void aaa_map_dec_ref(struct aaa_map *map) {
    if (aaa_ref_count_dec(&map->ref_count) == 0) {
        aaa_map_clear(map);
        free(map->buckets);
        free(map);
    }
}

void aaa_map_inc_ref(struct aaa_map *map) {
    aaa_ref_count_inc(&map->ref_count);
}

void aaa_map_clear(struct aaa_map *map) {
    if (map->size == 0) {
        return;
    }

    for (size_t b = 0; b < map->bucket_count; b++) {
        struct aaa_map_item *item = map->buckets[b];
        struct aaa_map_item *next;

        while (item) {
            next = item->next;
            aaa_variable_dec_ref(item->key);
            aaa_variable_dec_ref(item->value);
            free(item);
            item = next;
        }
    }
    map->size = 0;
}

void aaa_map_drop(struct aaa_map *map, const struct aaa_variable *key) {
    struct aaa_variable *popped = aaa_map_pop(map, key);
    aaa_variable_dec_ref(popped);
}

static float aaa_map_load_factor(const struct aaa_map *map) {
    return (float)(map->size) / map->bucket_count;
}

bool aaa_map_empty(const struct aaa_map *map) { return map->size == 0; }

static void aaa_map_rehash(struct aaa_map *map, size_t new_bucket_count) {
    if (map->bucket_count < new_bucket_count) {
        return;
    }

    size_t old_size = map->size;
    struct aaa_map_item **old_buckets = map->buckets;

    map->bucket_count = new_bucket_count;
    map->buckets = malloc(map->bucket_count * sizeof(*map->buckets));

    for (size_t b = 0; b < map->bucket_count; b++) {
        map->buckets[b] = NULL;
    }

    for (size_t b = 0; b < old_size; b++) {
        struct aaa_map_item *item = old_buckets[b];

        while (item) {
            struct aaa_map_item *next = item->next;

            size_t new_bucket = item->hash % new_bucket_count;
            item->next = map->buckets[new_bucket];
            map->buckets[new_bucket] = item;

            item = next;
        }
    }

    free(old_buckets);
}

static struct aaa_map_item *aaa_map_get_item(struct aaa_map *map,
                                             const struct aaa_variable *key) {
    size_t hash = aaa_variable_hash(key);
    size_t bucket = hash % map->bucket_count;
    struct aaa_map_item *item = map->buckets[bucket];

    while (item) {
        if (item->hash == hash && aaa_variable_equals(key, item->key)) {
            return item;
        }
        item = item->next;
    }

    return NULL;
}

struct aaa_variable *aaa_map_get(struct aaa_map *map,
                                 const struct aaa_variable *key) {
    struct aaa_map_item *item = aaa_map_get_item(map, key);

    if (item) {
        aaa_variable_inc_ref(item->value);
        return item->value;
    }

    return NULL;
}

bool aaa_map_has_key(struct aaa_map *map, const struct aaa_variable *key) {
    struct aaa_variable *value = aaa_map_get(map, key);

    if (value) {
        aaa_variable_dec_ref(value);
        return true;
    }

    return false;
}

struct aaa_variable *aaa_map_pop(struct aaa_map *map,
                                 const struct aaa_variable *key) {
    size_t hash = aaa_variable_hash(key);
    size_t bucket = hash % map->bucket_count;
    struct aaa_map_item **item_addr = &map->buckets[bucket];

    while (1) {
        struct aaa_map_item *item = *item_addr;
        if (!item) {
            return NULL;
        }

        if (item->hash == hash && aaa_variable_equals(key, item->key)) {
            struct aaa_variable *value = item->value;
            *item_addr = item->next;
            map->size--;

            aaa_variable_dec_ref(item->key);
            free(item);
            return value;
        }

        item_addr = &item->next;
    }

    return NULL;
}

void aaa_map_set(struct aaa_map *map, struct aaa_variable *key,
                 struct aaa_variable *new_value) {
    struct aaa_map_item *item = aaa_map_get_item(map, key);

    if (item) {
        aaa_variable_dec_ref(item->value);
    } else {
        item = malloc(sizeof(*item));

        item->hash = aaa_variable_hash(key);
        size_t bucket_id = item->hash % map->bucket_count;

        item->next = map->buckets[bucket_id];
        map->buckets[bucket_id] = item;

        item->key = key;
        aaa_variable_inc_ref(key);

        map->size++;

        if (aaa_map_load_factor(map) > 0.75) {
            aaa_map_rehash(map, map->bucket_count * 2);
        }
    }

    item->value = new_value;
    aaa_variable_inc_ref(new_value);
}

size_t aaa_map_size(const struct aaa_map *map) { return map->size; }

struct aaa_string *aaa_map_repr(const struct aaa_map *map) {
    struct aaa_buffer *buff = aaa_buffer_new();
    aaa_buffer_append(buff, "{");
    bool is_first = true;

    for (size_t i = 0; i < map->bucket_count; i++) {
        struct aaa_map_item *item = map->buckets[i];

        while (item) {
            if (is_first) {
                is_first = false;
            } else {
                aaa_buffer_append(buff, ", ");
            }

            struct aaa_string *key_repr = aaa_variable_repr(item->key);
            struct aaa_string *value_repr = aaa_variable_repr(item->value);

            aaa_buffer_append(buff, aaa_string_raw(key_repr));
            aaa_buffer_append(buff, ": ");
            aaa_buffer_append(buff, aaa_string_raw(value_repr));

            aaa_string_dec_ref(key_repr);
            aaa_string_dec_ref(value_repr);
            item = item->next;
        }
    }
    aaa_buffer_append(buff, "}");

    struct aaa_string *string = aaa_buffer_to_string(buff);
    aaa_buffer_dec_ref(buff);
    return string;
}

struct aaa_map *aaa_map_copy(struct aaa_map *map) {
    struct aaa_map *copy = aaa_map_new();
    for (size_t b = 0; b < map->bucket_count; b++) {
        struct aaa_map_item *item = map->buckets[b];

        while (item) {
            aaa_map_set(copy, item->key, item->value);
            item = item->next;
        }
    }

    return copy;
}

struct aaa_map_iter {
    struct aaa_ref_count ref_count;
    struct aaa_map *map;
    size_t next_bucket;
    struct aaa_map_item *next_item;
};

struct aaa_map_iter *aaa_map_iter_new(struct aaa_map *map) {
    struct aaa_map_iter *iter = malloc(sizeof(*iter));
    aaa_ref_count_init(&iter->ref_count);
    aaa_map_inc_ref(map);
    iter->map = map;
    iter->next_bucket = 1;
    iter->next_item = map->buckets[0];
    return iter;
}

void aaa_map_iter_dec_ref(struct aaa_map_iter *iter) {
    if (aaa_ref_count_dec(&iter->ref_count) == 0) {
        free(iter);
    }
}

void aaa_map_iter_inc_ref(struct aaa_map_iter *iter) {
    aaa_ref_count_inc(&iter->ref_count);
}

bool aaa_map_iter_next(struct aaa_map_iter *iter, struct aaa_variable **key,
                       struct aaa_variable **value) {
    while (true) {
        if (iter->next_bucket >= iter->map->bucket_count) {
            if (*key) {
                aaa_variable_dec_ref(*key);
                *key = NULL;
            }

            if (*value) {
                aaa_variable_dec_ref(*value);
                *value = NULL;
            }

            return false;
        }

        if (!iter->next_item) {
            iter->next_item = iter->map->buckets[iter->next_bucket];
            iter->next_bucket++;
        }

        break;
    }

    if (*key) {
        aaa_variable_dec_ref(*key);
    }

    if (*value) {
        aaa_variable_dec_ref(*value);
    }

    *key = iter->next_item->key;
    *value = iter->next_item->value;
    iter->next_item = iter->next_item->next;

    aaa_variable_inc_ref(*key);
    aaa_variable_inc_ref(*value);
    return true;
}


#include <malloc.h>
#include <stdlib.h>

#include "map.h"
#include "buffer.h"

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

struct aaa_map *aaa_map_new(void) {
    struct aaa_map *map = malloc(sizeof(*map));
    map->size = 0;
    map->bucket_count = 16;
    map->buckets = malloc(map->bucket_count * sizeof(*map->buckets));
    for (size_t b=0; b<map->bucket_count; b++) {
        map->buckets[b] = NULL;
    }
    return map;
}

void aaa_map_free(struct aaa_map *map) {
    aaa_map_clear(map);
    free(map->buckets);
    free(map);
}

void aaa_map_clear(struct aaa_map *map) {
    for (size_t b=0; b<map->bucket_count; b++) {
        struct aaa_map_item *item = map->buckets[b];
        struct aaa_map_item *next;

        while(item) {
            next = item->next;
            free(item);
            item = next;
        }
    }
    map->size = 0;
}

void aaa_map_copy(struct aaa_map *map, struct aaa_map *copy) {
    (void)map;
    (void)copy;

    fprintf(stderr, "aaa_map_copy is not implemented yet!\n");
    abort();
}

void aaa_map_drop(struct aaa_map *map, const struct aaa_variable *key) {
    aaa_map_pop(map, key);
}

bool aaa_map_empty(const struct aaa_map *map) {
    return map->size == 0;
}

struct aaa_variable *aaa_map_get(struct aaa_map *map, const struct aaa_variable *key) {
    size_t hash = aaa_variable_hash(key);
    size_t bucket = hash % map->bucket_count;
    struct aaa_map_item *item = map->buckets[bucket];

    while (item) {
        if (item->hash == hash && aaa_variable_equals(key, &item->key)) {
            return &item->value;
        }
        item = item->next;
    }

    return NULL;
}

bool aaa_map_has_key(struct aaa_map *map, const struct aaa_variable *key) {
    return aaa_map_get(map, key) != NULL;
}

struct aaa_variable *aaa_map_pop(struct aaa_map *map, const struct aaa_variable *key) {
    size_t hash = aaa_variable_hash(key);
    size_t bucket = hash % map->bucket_count;
    struct aaa_map_item **item_addr = &map->buckets[bucket];
    struct aaa_map_item *popped = NULL;

    while (1) {
        struct aaa_map_item *item = *item_addr;
        if (!item) {
            return NULL;
        }

        if (item->hash == hash && aaa_variable_equals(key, &item->key)) {
            popped = item;
            *item_addr = item->next;
            map->size--;
            return &popped->value;
        }

        item_addr = &item->next;
    }

    return NULL;
}

void aaa_map_set(struct aaa_map *map, const struct aaa_variable *key, const struct aaa_variable *new_value) {
    struct aaa_variable *value = aaa_map_get(map, key);

    if (value) {
        *value = *new_value;
        return;
    }

    struct aaa_map_item *item = malloc(sizeof(*item));
    item->key = *key;
    item->value = *new_value;
    item->hash = aaa_variable_hash(key);
    size_t bucket_id = item->hash % map->bucket_count;
    item->next = map->buckets[bucket_id];
    map->buckets[bucket_id] = item;
    map->size++;
}

size_t aaa_map_size(const struct aaa_map *map) {
    return map->size;
}

const char *aaa_map_repr(const struct aaa_map *map) {
    struct aaa_buffer *buff = aaa_buffer_new();
    aaa_buffer_append(buff, "{");
    bool is_first = true;

    for (size_t i=0; i<map->bucket_count; i++) {
        struct aaa_map_item *item = map->buckets[i];

        while (item) {
            if (is_first) {
                is_first = false;
            } else {
                aaa_buffer_append(buff, ", ");
            }

            const char *key_repr = aaa_variable_repr(&item->key);
            const char *value_repr = aaa_variable_repr(&item->value);
            aaa_buffer_append(buff, key_repr);
            aaa_buffer_append(buff, ": ");
            aaa_buffer_append(buff, value_repr);

            item = item->next;
        }
    }
    aaa_buffer_append(buff, "}");

    const char *repr = aaa_buffer_to_string(buff);
    aaa_buffer_dec_ref(buff);
    return repr;
}

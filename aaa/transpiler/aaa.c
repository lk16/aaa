#include <malloc.h>
#include <assert.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>
#include <netinet/in.h>
#include <string.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/types.h>
#include <sys/socket.h>

#include "aaa.h"

static void aaa_variable_check_kind(const struct aaa_variable *var, enum aaa_kind kind) {
    if (var->kind != kind) {
        fprintf(stderr, "Aaa type error\n");
        abort();
    }
}

static char *aaa_variable_repr(const struct aaa_variable *var);

static char *aaa_vec_repr(const struct aaa_vector *vec) {
    struct aaa_buffer buff;
    aaa_buffer_init(&buff);
    aaa_buff_append(&buff, "[");

    for (size_t i=0; i<vec->size; i++) {
        struct aaa_variable *item = vec->data + i;

        char *item_repr = aaa_variable_repr(item);
        aaa_buff_append(&buff, item_repr);

        if (i != vec->size - 1) {
            aaa_buff_append(&buff, ", ");
        }
    }
    aaa_buff_append(&buff, "]");

    return buff.data;
}

static char *aaa_variable_repr(const struct aaa_variable *var) {
    switch (var->kind) {
        case AAA_BOOLEAN:
            if (var->boolean) {
                return "true";
            } else {
                return "false";
            }
        case AAA_INTEGER:
            (void)0;
            size_t buff_size = snprintf(NULL, 0, "%d", var->integer);
            char *buff = malloc(buff_size + 1);
            snprintf(buff, buff_size + 1, "%d", var->integer);
            return buff;
        case AAA_STRING:
            fprintf(stderr, "aaa_variable_repr Printing string repr is not implemented\n");
            abort();
            break;
        case AAA_VECTOR:
            return aaa_vec_repr(var->vector);
        default:
            fprintf(stderr, "aaa_variable_repr Unhandled variable kind\n");
            abort();
    }
}

static size_t aaa_variable_hash(const struct aaa_variable *var) {
    switch (var->kind) {
        case AAA_BOOLEAN:
            if (var->boolean) {
                return 1;
            } else {
                return 0;
            }
        case AAA_INTEGER:
            return (var->integer ^ 0x123456789) + (var->integer << 13) + (var->integer >> 17);
        case AAA_STRING:
            (void)0;
            size_t hash = 0;
            const char *c = var->string;
            while (c) {
                hash = (hash * 123457) + *c;
                c++;
            }
            return hash;
        case AAA_VECTOR:
            fprintf(stderr, "Cannot hash a vector!\n");
            abort();
        default:
            fprintf(stderr, "aaa_variable_hash Unhandled variable kind\n");
            abort();
    }
}

static bool aaa_variable_equals(const struct aaa_variable *lhs, const struct aaa_variable *rhs) {
    if (lhs->kind != rhs->kind) {
        return false;
    }

    switch (lhs->kind) {
        case AAA_BOOLEAN:
            return lhs->boolean == rhs->boolean;
        case AAA_INTEGER:
            return lhs->integer == rhs->integer;
        case AAA_STRING:
            return strcmp(lhs->string, rhs->string) == 0;
        case AAA_VECTOR:
            // TODO use vector equality function when present
            if (lhs->vector->size != rhs->vector->size) {
                return false;
            }
            for (size_t i=0; i<lhs->vector->size; i++) {
                struct aaa_variable *lhs_item = NULL, *rhs_item = NULL;
                aaa_vector_get(lhs->vector, i, lhs_item);
                aaa_vector_get(rhs->vector, i, rhs_item);
                if (!aaa_variable_equals(lhs_item, rhs_item)) {
                    return false;
                }
            }
            return true;
        default:
            fprintf(stderr, "aaa_variable_equals Unhandled variable kind\n");
            abort();
    }
}

void aaa_buffer_init(struct aaa_buffer *buff) {
    buff->max_size = 1024;
    buff->data = malloc(buff->max_size * sizeof(char));
    buff->size = 0;
    buff->data[buff->size] = '\0';
}

void aaa_buff_append(struct aaa_buffer *buff, const char *str) {
    size_t len = strlen(str);

    while (buff->size + len + 1 > buff->max_size) {
        char *new_data = malloc(2 * buff->max_size * sizeof(char));
        memcpy(new_data, buff->data, buff->max_size);
        free(buff->data);
        buff->data = new_data;
        buff->max_size *= 2;
    }

    memcpy(buff->data + buff->size, str, len);
    buff->size += len;
    buff->data[buff->size] = '\0';
}

void aaa_stack_not_implemented(struct aaa_stack *stack, const char *aaa_func_name) {
    (void)stack;
    fprintf(stderr, "%s is not implemented yet!\n", aaa_func_name);
    abort();
}

static void aaa_stack_prevent_underflow(const struct aaa_stack *stack, size_t pop_count) {
    if (stack->size < pop_count) {
        fprintf(stderr, "Aaa stack underflow\n");
        abort();
    }
}

static void aaa_stack_prevent_overflow(const struct aaa_stack *stack, size_t push_count) {
     if (stack->size + push_count >= stack->max_size) {
        fprintf(stderr, "Aaa stack overflow\n");
        abort();
    }
}

void aaa_stack_init(struct aaa_stack *stack) {
    stack->size = 0;
    stack->max_size = 1024;
    stack->data = malloc(stack->max_size * sizeof(*stack->data));
}

void aaa_stack_free(struct aaa_stack *stack) {
    free(stack->data);
}

static struct aaa_variable *aaa_stack_top(struct aaa_stack *stack) {
    return stack->data + stack->size - 1;
}

static struct aaa_variable *aaa_stack_push(struct aaa_stack *stack) {
    aaa_stack_prevent_overflow(stack, 1);

    stack->size++;
    return aaa_stack_top(stack);
}

void aaa_stack_push_variable(struct aaa_stack *stack, struct aaa_variable *variable) {
    struct aaa_variable *top = aaa_stack_push(stack);
    *top = *variable;
}

struct aaa_variable *aaa_stack_pop(struct aaa_stack *stack) {
    aaa_stack_prevent_underflow(stack, 1);

    struct aaa_variable *popped = aaa_stack_top(stack);
    stack->size--;
    return popped;
}

void aaa_stack_push_int(struct aaa_stack *stack, int value) {
    struct aaa_variable *top = aaa_stack_push(stack);
    top->kind = AAA_INTEGER;
    top->integer = value;
}

void aaa_stack_push_str(struct aaa_stack *stack, const char *value) {
    struct aaa_variable *top = aaa_stack_push(stack);
    top->kind = AAA_STRING;
    top->string = value;
}

void aaa_stack_push_bool(struct aaa_stack *stack, bool value) {
    struct aaa_variable *top = aaa_stack_push(stack);
    top->kind = AAA_BOOLEAN;
    top->boolean = value;
}

bool aaa_stack_pop_bool(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    aaa_variable_check_kind(top, AAA_BOOLEAN);
    return top->boolean;
}

static int aaa_stack_pop_int(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    aaa_variable_check_kind(top, AAA_INTEGER);
    return top->integer;
}

static const char *aaa_stack_pop_str(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    aaa_variable_check_kind(top, AAA_STRING);
    return top->string;
}

struct aaa_vector *aaa_stack_pop_vec(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    aaa_variable_check_kind(top, AAA_VECTOR);
    return top->vector;
}

void aaa_stack_dup(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_top(stack);
    struct aaa_variable *dupped = aaa_stack_push(stack);

    *dupped = *top;
}

void aaa_stack_swap(struct aaa_stack *stack) {
    aaa_stack_prevent_underflow(stack, 2);

    struct aaa_variable *top = aaa_stack_top(stack);
    struct aaa_variable *below = top - 1;

    struct aaa_variable temp = *top;
    *top = *below;
    *below = temp;
}

void aaa_stack_assert(struct aaa_stack *stack) {
    bool value = aaa_stack_pop_bool(stack);

    if (!value) {
        printf("Assertion failure!\n");
        abort();
    }
}

void aaa_stack_over(struct aaa_stack *stack) {
    aaa_stack_prevent_underflow(stack, 2);
    aaa_stack_push(stack);

    struct aaa_variable *top = aaa_stack_top(stack);
    struct aaa_variable *original = top - 2;

    *original = *top;
}

void aaa_stack_rot(struct aaa_stack *stack) {
    aaa_stack_prevent_underflow(stack, 3);

    struct aaa_variable *c = aaa_stack_top(stack);
    struct aaa_variable *b = c - 1;
    struct aaa_variable *a = c - 2;

    struct aaa_variable tmp = *a;
    *a = *b;
    *b = *c;
    *c = tmp;
}

void aaa_stack_plus(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_int(stack, lhs + rhs);
}

void aaa_stack_minus(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_int(stack, lhs - rhs);
}

void aaa_stack_multiply(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_int(stack, lhs * rhs);
}

void aaa_stack_divide(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);

    if (rhs == 0) {
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_bool(stack, false);
    } else {
        aaa_stack_push_int(stack, lhs / rhs);
        aaa_stack_push_bool(stack, true);
    }
}

void aaa_stack_repr(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    char *repr = aaa_variable_repr(top);
    aaa_stack_push_str(stack, repr);
}

void aaa_stack_print(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);

    const char *printed;

    if (top->kind == AAA_STRING) {
        printed = top->string;
    } else {
        printed = aaa_variable_repr(top);
    }
    printf("%s", printed);
}

void aaa_stack_drop(struct aaa_stack *stack) {
    aaa_stack_pop(stack);
}

void aaa_stack_less(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_bool(stack, lhs < rhs);
}

void aaa_stack_less_equal(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_bool(stack, lhs <= rhs);
}

void aaa_stack_unequal(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_bool(stack, lhs != rhs);
}

void aaa_stack_greater(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_bool(stack, lhs > rhs);
}

void aaa_stack_greater_equal(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_bool(stack, lhs >= rhs);
}

void aaa_stack_modulo(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);

    if (rhs == 0) {
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_bool(stack, false);
    } else {
        aaa_stack_push_int(stack, lhs % rhs);
        aaa_stack_push_bool(stack, true);
    }
}

void aaa_stack_equals(struct aaa_stack *stack) {
    int rhs = aaa_stack_pop_int(stack);
    int lhs = aaa_stack_pop_int(stack);
    aaa_stack_push_bool(stack, lhs == rhs);
}

void aaa_stack_or(struct aaa_stack *stack) {
    bool rhs = aaa_stack_pop_bool(stack);
    bool lhs = aaa_stack_pop_bool(stack);
    aaa_stack_push_bool(stack, lhs || rhs);
}

void aaa_stack_and(struct aaa_stack *stack) {
    bool rhs = aaa_stack_pop_bool(stack);
    bool lhs = aaa_stack_pop_bool(stack);
    aaa_stack_push_bool(stack, lhs && rhs);
}

void aaa_stack_socket(struct aaa_stack *stack) {
    int protocol = aaa_stack_pop_int(stack);
    int type = aaa_stack_pop_int(stack);
    int family = aaa_stack_pop_int(stack);

    int fd = socket(family, type, protocol);

    if (fd < 0) {
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_bool(stack, false);
    } else {
        aaa_stack_push_int(stack, fd);
        aaa_stack_push_bool(stack, true);
    }
}

void aaa_stack_not(struct aaa_stack *stack) {
    bool value = aaa_stack_pop_bool(stack);
    aaa_stack_push_bool(stack, !value);
}

void aaa_stack_exit(struct aaa_stack *stack) {
    int code = aaa_stack_pop_int(stack);
    exit(code);
}

void aaa_stack_write(struct aaa_stack *stack) {
    const char *data = aaa_stack_pop_str(stack);
    int fd = aaa_stack_pop_int(stack);

    // TODO make string smarter so we keep its length cached
    int written = write(fd, data, strlen(data));

    if (written < 0) {
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_bool(stack, false);
    } else {
        aaa_stack_push_int(stack, written);
        aaa_stack_push_bool(stack, true);
    }
}

void aaa_stack_connect(struct aaa_stack *stack) {
    int port = aaa_stack_pop_int(stack);
    const char *domain_name = aaa_stack_pop_str(stack);
    int fd = aaa_stack_pop_int(stack);

    struct addrinfo* addr_info = NULL;

    // prevent buffer overflow
    if (port >= 65536 || port < 0) {
        aaa_stack_push_bool(stack, false);
        return;
    }

    char service[6];

    snprintf(service, 6, "%d", port);

    if (getaddrinfo(domain_name, service, NULL, &addr_info) != 0) {
        aaa_stack_push_bool(stack, false);
        return;
    }

    int success = connect(fd, (struct sockaddr*) addr_info->ai_addr, sizeof(*addr_info));

    freeaddrinfo(addr_info);

    if (success == 0) {
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_bool(stack, false);
    }
}

void aaa_stack_read(struct aaa_stack *stack) {
    int n = aaa_stack_pop_int(stack);
    int fd = aaa_stack_pop_int(stack);

    // TODO we create a C-string here, consider using a new buffer type
    char *buff = malloc((n + 1) * sizeof(char));

    int bytes_read = read(fd, buff, n);
    buff[bytes_read] = '\0';

    aaa_stack_push_str(stack, buff);

    if (bytes_read < 0) {
        aaa_stack_push_bool(stack, false);
    } else {
        aaa_stack_push_bool(stack, true);
    }
}

void aaa_stack_bind(struct aaa_stack *stack) {
    int port = aaa_stack_pop_int(stack);
    const char *host = aaa_stack_pop_str(stack);
    int fd = aaa_stack_pop_int(stack);

    struct addrinfo* addr_info = NULL;

    // prevent buffer overflow
    if (port >= 65536 || port < 0) {
        aaa_stack_push_bool(stack, false);
        return;
    }

    char service[6];

    snprintf(service, 6, "%d", port);

    if (getaddrinfo(host, service, NULL, &addr_info) != 0) {
        aaa_stack_push_bool(stack, false);
        return;
    }

    int bind_status = bind(fd, (struct sockaddr*) addr_info->ai_addr, sizeof(*addr_info));

    freeaddrinfo(addr_info);

    if (bind_status == 0) {
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_bool(stack, false);
    }
}

void aaa_stack_listen(struct aaa_stack *stack) {
    int backlog = aaa_stack_pop_int(stack);
    int fd = aaa_stack_pop_int(stack);

    if (listen(fd, backlog) == 0) {
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_bool(stack, false);
    }
}

void aaa_stack_accept(struct aaa_stack *stack) {
    int fd = aaa_stack_pop_int(stack);

    struct sockaddr_in client_socket;
    socklen_t client_socket_len = sizeof(struct sockaddr_in);

    int client_socket_fd = accept(fd, (struct sockaddr *) &client_socket, &client_socket_len);

    if (client_socket_fd != -1) {
        char *client_ip_addr = malloc((INET6_ADDRSTRLEN + 1) * sizeof(char));
        int client_port;

        switch (client_socket.sin_family) {
            case AF_INET: {
                struct sockaddr_in *sin = (struct sockaddr_in*) &client_socket;
                inet_ntop(AF_INET, &sin->sin_addr, client_ip_addr, INET6_ADDRSTRLEN);
                client_port = sin->sin_port;
                break;
            }
            case AF_INET6: {
                struct sockaddr_in6 *sin = (struct sockaddr_in6*) &client_socket;
                inet_ntop(AF_INET6, &sin->sin6_addr, client_ip_addr, INET6_ADDRSTRLEN);
                client_port = sin->sin6_port;
                break;
            }
            default:
                abort();
        }

        aaa_stack_push_str(stack, client_ip_addr);
        aaa_stack_push_int(stack, client_port);
        aaa_stack_push_int(stack, client_socket_fd);
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_str(stack, "");
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_bool(stack, false);
    }
}

void aaa_stack_nop(struct aaa_stack *stack) {
    (void)stack;
}

void aaa_stack_str_equals(struct aaa_stack *stack) {
    const char *lhs = aaa_stack_pop_str(stack);
    const char *rhs = aaa_stack_pop_str(stack);
    bool equal = strcmp(lhs, rhs) == 0;
    aaa_stack_push_bool(stack, equal);
}

void aaa_vector_init(struct aaa_vector *vec) {
    vec->size = 0;
    vec->max_size = 16;
    vec->data = malloc(vec->max_size * sizeof(*vec->data));
}
void aaa_vector_free(struct aaa_vector *vec) {
    free(vec->data);
}

void aaa_vector_clear(struct aaa_vector *vec) {
    vec->size = 0;
}

void aaa_vector_copy(struct aaa_vector *vec, struct aaa_vector *copy) {
    (void)vec;
    (void)copy;

    fprintf(stderr, "aaa_vector_copy is not implemented yet!\n");
    abort();
}

bool aaa_vector_empty(const struct aaa_vector *vec) {
    return vec->size == 0;
}

void aaa_vector_get(struct aaa_vector *vec, size_t offset, struct aaa_variable *result) {
    if (offset >= vec->size) {
        fprintf(stderr, "aaa_vector_get out of range\n");
        abort();
    }

    *result = vec->data[offset];
}

void aaa_vector_pop(struct aaa_vector *vec, struct aaa_variable *popped) {
    if (vec->size == 0) {
        fprintf(stderr, "aaa_vector_pop out of range\n");
        abort();
    }

    *popped = vec->data[vec->size - 1];
    vec->size--;
}

static void aaa_vector_resize(struct aaa_vector *vec, size_t new_size) {
    struct aaa_variable *new_data = malloc(new_size * sizeof(*new_data));
    memcpy(new_data, vec->data, vec->max_size * sizeof(*vec->data));
    free(vec->data);
    vec->data = new_data;
    vec->size = new_size;
}

void aaa_vector_push(struct aaa_vector *vec, struct aaa_variable *pushed) {
    if(vec->size == vec->max_size) {
        aaa_vector_resize(vec, 2 * vec->size);
    }

    vec->data[vec->size] = *pushed;
    vec->size++;
}

void aaa_vector_set(struct aaa_vector *vec, size_t offset, struct aaa_variable *value) {
    if (offset >= vec->size) {
        fprintf(stderr, "aaa_vector_set out of range\n");
        abort();
    }

    vec->data[offset] = *value;
}

size_t aaa_vector_size(const struct aaa_vector *vec) {
    return vec->size;
}

void aaa_stack_push_vec(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_push(stack);
    top->kind = AAA_VECTOR;
    top->vector = malloc(sizeof(struct aaa_vector));
    aaa_vector_init(top->vector);
}

void aaa_stack_vec_push(struct aaa_stack *stack) {
    struct aaa_variable *pushed = aaa_stack_pop(stack);
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);

    aaa_vector_push(vec, pushed);
}

void aaa_stack_vec_pop(struct aaa_stack *stack) {
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);
    struct aaa_variable *top = aaa_stack_push(stack);
    aaa_vector_pop(vec, top);
}

void aaa_stack_vec_get(struct aaa_stack *stack) {
    int offset = aaa_stack_pop_int(stack);
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);
    struct aaa_variable *top = aaa_stack_push(stack);
    aaa_vector_get(vec, offset, top);
}

void aaa_stack_vec_set(struct aaa_stack *stack) {
    struct aaa_variable *value = aaa_stack_pop(stack);
    int offset = aaa_stack_pop_int(stack);
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);

    aaa_vector_set(vec, offset, value);
}

void aaa_stack_vec_size(struct aaa_stack *stack) {
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);
    int size = aaa_vector_size(vec);
    aaa_stack_push_int(stack, size);
}

void aaa_stack_vec_empty(struct aaa_stack *stack) {
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);
    int empty = aaa_vector_empty(vec);
    aaa_stack_push_bool(stack, empty);
}

void aaa_stack_vec_clear(struct aaa_stack *stack) {
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);
    aaa_vector_clear(vec);
}

void aaa_map_init(struct aaa_map *map) {
    map->size = 0;
    map->bucket_count = 16;
    map->buckets = malloc(map->bucket_count * sizeof(*map->buckets));
    for (size_t b=0; b<map->bucket_count; b++) {
        map->buckets[b] = NULL;
    }
}

void aaa_map_free(struct aaa_map *map) {
    aaa_map_clear(map);
    free(map->buckets);
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
        }
    }

    if (popped) {
        map->size--;
        return &popped->value;
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
    item->value = *value;
    item->hash = aaa_variable_hash(key);
    size_t bucket_id = item->hash % map->bucket_count;
    item->next = map->buckets[bucket_id];
    map->buckets[bucket_id] = item;
}

size_t aaa_map_size(const struct aaa_map *map) {
    return map->size;
}

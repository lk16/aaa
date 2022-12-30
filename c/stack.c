#include <arpa/inet.h>
#include <fcntl.h>
#include <limits.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "map.h"
#include "stack.h"
#include "str.h"
#include "struct.h"
#include "var.h"
#include "vector.h"

extern char **environ;

void aaa_stack_not_implemented(struct aaa_stack *stack,
                               const char *aaa_func_name) {
    (void)stack;
    fprintf(stderr, "%s is not implemented yet!\n", aaa_func_name);
    abort();
}

static void aaa_stack_prevent_underflow(const struct aaa_stack *stack,
                                        size_t pop_count) {
    if (stack->size < pop_count) {
        fprintf(stderr, "Aaa stack underflow\n");
        abort();
    }
}

static void aaa_stack_prevent_overflow(
    const struct aaa_stack *stack,
    size_t push_count) { // TODO remove this and re-allocate the stack if it
                         // gets too big
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

void aaa_stack_free(struct aaa_stack *stack) { free(stack->data); }

static struct aaa_variable *aaa_stack_top(struct aaa_stack *stack) {
    return stack->data[stack->size - 1];
}

void aaa_stack_push(struct aaa_stack *stack, struct aaa_variable *variable) {
    aaa_stack_prevent_overflow(stack, 1);
    stack->data[stack->size] = variable;
    stack->size++;
}

struct aaa_variable *aaa_stack_pop(struct aaa_stack *stack) {
    aaa_stack_prevent_underflow(stack, 1);

    struct aaa_variable *popped = aaa_stack_top(stack);
    stack->size--;

    return popped;
}

void aaa_stack_push_int(struct aaa_stack *stack, int value) {
    struct aaa_variable *var = aaa_variable_new_int(value);
    aaa_stack_push(stack, var);
}

void aaa_stack_push_str(struct aaa_stack *stack, struct aaa_string *value) {
    struct aaa_variable *var = aaa_variable_new_str(value);
    aaa_stack_push(stack, var);
}

void aaa_stack_push_str_raw(struct aaa_stack *stack, const char *raw,
                            bool freeable) {
    struct aaa_string *string = aaa_string_new(raw, freeable);
    aaa_stack_push_str(stack, string);
}

void aaa_stack_push_bool(struct aaa_stack *stack, bool value) {
    struct aaa_variable *var = aaa_variable_new_bool(value);
    aaa_stack_push(stack, var);
}

bool aaa_stack_pop_bool(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    bool value = aaa_variable_get_bool(top);
    aaa_variable_dec_ref(top);
    return value;
}

struct aaa_struct *aaa_stack_pop_struct(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    struct aaa_struct *s = aaa_variable_get_struct(top);

    aaa_struct_inc_ref(s);
    aaa_variable_dec_ref(top);

    return s;
}

void aaa_stack_push_struct(struct aaa_stack *stack, struct aaa_struct *s) {
    struct aaa_variable *var = aaa_variable_new_struct(s);
    aaa_stack_push(stack, var);
}

static int aaa_stack_pop_int(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    int value = aaa_variable_get_int(top);
    aaa_variable_dec_ref(top);
    return value;
}

static struct aaa_string *aaa_stack_pop_str(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    struct aaa_string *value = aaa_variable_get_str(top);
    aaa_string_inc_ref(value);
    aaa_variable_dec_ref(top);
    return value;
}

static struct aaa_vector *aaa_stack_pop_vec(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    struct aaa_vector *vector = aaa_variable_get_vector(top);

    aaa_vector_inc_ref(vector);
    aaa_variable_dec_ref(top);

    return vector;
}

static struct aaa_map *aaa_stack_pop_map(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    struct aaa_map *map = aaa_variable_get_map(top);

    aaa_map_inc_ref(map);
    aaa_variable_dec_ref(top);

    return map;
}

void aaa_stack_dup(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_top(stack);
    aaa_stack_push(stack, top);
    aaa_variable_inc_ref(top);
}

void aaa_stack_swap(struct aaa_stack *stack) {
    aaa_stack_prevent_underflow(stack, 2);

    struct aaa_variable *a = aaa_stack_pop(stack);
    struct aaa_variable *b = aaa_stack_pop(stack);

    aaa_stack_push(stack, a);
    aaa_stack_push(stack, b);
}

void aaa_stack_assert(struct aaa_stack *stack) {
    bool value = aaa_stack_pop_bool(stack);

    if (!value) {
        fprintf(stderr, "Assertion failure!\n");
        fflush(stderr);
        abort();
    }
}

void aaa_stack_over(struct aaa_stack *stack) {
    aaa_stack_prevent_underflow(stack, 2);

    struct aaa_variable *copied = stack->data[stack->size - 2];
    aaa_stack_push(stack, copied);

    aaa_variable_inc_ref(copied);
}

void aaa_stack_rot(struct aaa_stack *stack) {
    struct aaa_variable *c = aaa_stack_pop(stack);
    struct aaa_variable *b = aaa_stack_pop(stack);
    struct aaa_variable *a = aaa_stack_pop(stack);

    aaa_stack_push(stack, b);
    aaa_stack_push(stack, c);
    aaa_stack_push(stack, a);
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
    struct aaa_string *repr = aaa_variable_repr(top);
    aaa_stack_push_str(stack, repr);

    aaa_variable_dec_ref(top);
}

void aaa_stack_print(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    struct aaa_string *printed = aaa_variable_printed(top);

    const char *raw = aaa_string_raw(printed);
    printf("%s", raw);
    fflush(stdout);

    aaa_string_dec_ref(printed);
    aaa_variable_dec_ref(top);
}

void aaa_stack_drop(struct aaa_stack *stack) {
    struct aaa_variable *popped = aaa_stack_pop(stack);
    aaa_variable_dec_ref(popped);
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
    struct aaa_string *data = aaa_stack_pop_str(stack);
    int fd = aaa_stack_pop_int(stack);

    const char *data_raw = aaa_string_raw(data);
    size_t length = aaa_string_len(data);

    int written = (int)write(fd, data_raw, length);

    if (written < 0) {
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_bool(stack, false);
    } else {
        aaa_stack_push_int(stack, written);
        aaa_stack_push_bool(stack, true);
    }

    aaa_string_dec_ref(data);
}

void aaa_stack_connect(struct aaa_stack *stack) {
    int port = aaa_stack_pop_int(stack);
    struct aaa_string *domain_name = aaa_stack_pop_str(stack);
    int fd = aaa_stack_pop_int(stack);

    const char *domain_name_raw = aaa_string_raw(domain_name);

    struct addrinfo *addr_info = NULL;

    // prevent buffer overflow
    if (port >= 65536 || port < 0) {
        aaa_stack_push_bool(stack, false);
        return;
    }

    char service[6];

    snprintf(service, 6, "%d", port);

    if (getaddrinfo(domain_name_raw, service, NULL, &addr_info) != 0) {
        aaa_stack_push_bool(stack, false);
        return;
    }

    int success =
        connect(fd, (struct sockaddr *)addr_info->ai_addr, sizeof(*addr_info));

    freeaddrinfo(addr_info);

    if (success == 0) {
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_bool(stack, false);
    }

    aaa_string_dec_ref(domain_name);
}

void aaa_stack_read(struct aaa_stack *stack) {
    int n = aaa_stack_pop_int(stack);
    int fd = aaa_stack_pop_int(stack);

    // TODO we create a C-string here, consider using a new buffer type
    char *buff = malloc((long unsigned)(n + 1) * sizeof(char));

    int bytes_read = (int)read(fd, buff, (size_t)n);
    buff[bytes_read] = '\0';

    aaa_stack_push_str_raw(stack, buff, true);

    if (bytes_read < 0) {
        aaa_stack_push_bool(stack, false);
    } else {
        aaa_stack_push_bool(stack, true);
    }
}

void aaa_stack_bind(struct aaa_stack *stack) {
    int port = aaa_stack_pop_int(stack);
    struct aaa_string *host = aaa_stack_pop_str(stack);
    int fd = aaa_stack_pop_int(stack);

    const char *host_raw = aaa_string_raw(host);

    struct addrinfo *addr_info = NULL;

    // prevent buffer overflow
    if (port >= 65536 || port < 0) {
        aaa_stack_push_bool(stack, false);
        return;
    }

    char service[6];

    snprintf(service, 6, "%d", port);

    if (getaddrinfo(host_raw, service, NULL, &addr_info) != 0) {
        aaa_stack_push_bool(stack, false);
        return;
    }

    int bind_status =
        bind(fd, (struct sockaddr *)addr_info->ai_addr, sizeof(*addr_info));

    freeaddrinfo(addr_info);

    if (bind_status == 0) {
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_bool(stack, false);
    }

    aaa_string_dec_ref(host);
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

    int client_socket_fd =
        accept(fd, (struct sockaddr *)&client_socket, &client_socket_len);

    if (client_socket_fd != -1) {
        char *client_ip_addr = malloc((INET6_ADDRSTRLEN + 1) * sizeof(char));
        int client_port;

        switch (client_socket.sin_family) {
            case AF_INET: {
                struct sockaddr_in *sin = (struct sockaddr_in *)&client_socket;
                inet_ntop(AF_INET, &sin->sin_addr, client_ip_addr,
                          INET6_ADDRSTRLEN);
                client_port = sin->sin_port;
                break;
            }
            case AF_INET6: {
                struct sockaddr_in6 *sin =
                    (struct sockaddr_in6 *)&client_socket;
                inet_ntop(AF_INET6, &sin->sin6_addr, client_ip_addr,
                          INET6_ADDRSTRLEN);
                client_port = sin->sin6_port;
                break;
            }
            default:
                abort();
        }

        aaa_stack_push_str_raw(stack, client_ip_addr, true);
        aaa_stack_push_int(stack, client_port);
        aaa_stack_push_int(stack, client_socket_fd);
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_str_raw(stack, "", false);
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_bool(stack, false);
    }
}

void aaa_stack_nop(struct aaa_stack *stack) { (void)stack; }

void aaa_stack_push_vec_empty(struct aaa_stack *stack) {
    struct aaa_vector *vector = aaa_vector_new();
    aaa_stack_push_vec(stack, vector);
}

void aaa_stack_push_vec(struct aaa_stack *stack, struct aaa_vector *vector) {
    struct aaa_variable *var = aaa_variable_new_vector(vector);
    aaa_stack_push(stack, var);
}

void aaa_stack_vec_push(struct aaa_stack *stack) {
    struct aaa_variable *pushed = aaa_stack_pop(stack);
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);

    aaa_vector_push(vec, pushed);

    aaa_vector_dec_ref(vec);
    aaa_variable_dec_ref(pushed);
}

void aaa_stack_vec_pop(struct aaa_stack *stack) {
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);
    struct aaa_variable *popped = aaa_vector_pop(vec);

    aaa_stack_push(stack, popped);

    aaa_vector_dec_ref(vec);
}

void aaa_stack_vec_get(struct aaa_stack *stack) {
    int offset = aaa_stack_pop_int(stack);
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);
    struct aaa_variable *gotten = aaa_vector_get(vec, (size_t)offset);

    aaa_stack_push(stack, gotten);

    aaa_variable_inc_ref(gotten);
    aaa_vector_dec_ref(vec);
}

void aaa_stack_vec_set(struct aaa_stack *stack) {
    struct aaa_variable *value = aaa_stack_pop(stack);
    int offset = aaa_stack_pop_int(stack);
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);

    bool success = aaa_vector_set(vec, (size_t)offset, value);
    aaa_stack_push_bool(stack, success);

    aaa_vector_dec_ref(vec);
}

void aaa_stack_vec_size(struct aaa_stack *stack) {
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);

    size_t size = aaa_vector_size(vec);
    aaa_stack_push_int(stack, (int)size);

    aaa_vector_dec_ref(vec);
}

void aaa_stack_vec_empty(struct aaa_stack *stack) {
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);

    int empty = aaa_vector_empty(vec);
    aaa_stack_push_bool(stack, empty);

    aaa_vector_dec_ref(vec);
}

void aaa_stack_vec_clear(struct aaa_stack *stack) {
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);

    aaa_vector_clear(vec);

    aaa_vector_dec_ref(vec);
}

void aaa_stack_push_map_empty(struct aaa_stack *stack) {
    struct aaa_map *map = aaa_map_new();
    aaa_stack_push_map(stack, map);
}

void aaa_stack_push_map(struct aaa_stack *stack, struct aaa_map *map) {
    struct aaa_variable *var = aaa_variable_new_map(map);
    aaa_stack_push(stack, var);
}

void aaa_stack_map_set(struct aaa_stack *stack) {
    struct aaa_variable *value = aaa_stack_pop(stack);
    struct aaa_variable *key = aaa_stack_pop(stack);
    struct aaa_map *map = aaa_stack_pop_map(stack);

    aaa_map_set(map, key, value);

    aaa_map_dec_ref(map);
    aaa_variable_dec_ref(key);
    aaa_variable_dec_ref(value);
}

void aaa_stack_map_get(struct aaa_stack *stack) {
    struct aaa_variable *key = aaa_stack_pop(stack);
    struct aaa_map *map = aaa_stack_pop_map(stack);

    struct aaa_variable *value = aaa_map_get(map, key);

    if (!value) {
        // TODO this requires changes in signature of map:get
        fprintf(stderr, "map:get does not handle missing keys\n");
        abort();
    }

    aaa_stack_push(stack, value);

    aaa_map_dec_ref(map);
    aaa_variable_dec_ref(key);
}

void aaa_stack_map_has_key(struct aaa_stack *stack) {
    struct aaa_variable *key = aaa_stack_pop(stack);
    struct aaa_map *map = aaa_stack_pop_map(stack);

    bool has_key = aaa_map_has_key(map, key);
    aaa_stack_push_bool(stack, has_key);

    aaa_map_dec_ref(map);
    aaa_variable_dec_ref(key);
}

void aaa_stack_map_size(struct aaa_stack *stack) {
    struct aaa_map *map = aaa_stack_pop_map(stack);

    size_t size = aaa_map_size(map);
    aaa_stack_push_int(stack, (int)size);

    aaa_map_dec_ref(map);
}

void aaa_stack_map_empty(struct aaa_stack *stack) {
    struct aaa_map *map = aaa_stack_pop_map(stack);

    bool is_empty = aaa_map_empty(map);
    aaa_stack_push_bool(stack, is_empty);

    aaa_map_dec_ref(map);
}

void aaa_stack_map_clear(struct aaa_stack *stack) {
    struct aaa_map *map = aaa_stack_pop_map(stack);

    aaa_map_clear(map);

    aaa_map_dec_ref(map);
}

void aaa_stack_map_pop(struct aaa_stack *stack) {
    struct aaa_variable *key = aaa_stack_pop(stack);
    struct aaa_map *map = aaa_stack_pop_map(stack);

    struct aaa_variable *value = aaa_map_pop(map, key);

    if (!value) {
        // TODO this requires changes in signature of map:pop
        fprintf(stderr, "map:pop does not handle missing keys\n");
        abort();
    }

    aaa_stack_push(stack, value);

    aaa_variable_dec_ref(key);
    aaa_map_dec_ref(map);
}

void aaa_stack_map_drop(struct aaa_stack *stack) {
    struct aaa_variable *key = aaa_stack_pop(stack);
    struct aaa_map *map = aaa_stack_pop_map(stack);

    aaa_map_drop(map, key);

    aaa_variable_dec_ref(key);
    aaa_map_dec_ref(map);
}

void aaa_stack_str_append(struct aaa_stack *stack) {
    struct aaa_string *rhs = aaa_stack_pop_str(stack);
    struct aaa_string *lhs = aaa_stack_pop_str(stack);

    struct aaa_string *combined = aaa_string_append(lhs, rhs);
    aaa_stack_push_str(stack, combined);

    aaa_string_dec_ref(lhs);
    aaa_string_dec_ref(rhs);
}

void aaa_stack_str_contains(struct aaa_stack *stack) {
    struct aaa_string *search = aaa_stack_pop_str(stack);
    struct aaa_string *string = aaa_stack_pop_str(stack);

    bool contained = aaa_string_contains(string, search);
    aaa_stack_push_bool(stack, contained);

    aaa_string_dec_ref(search);
    aaa_string_dec_ref(string);
}

void aaa_stack_str_equals(struct aaa_stack *stack) {
    struct aaa_string *rhs = aaa_stack_pop_str(stack);
    struct aaa_string *lhs = aaa_stack_pop_str(stack);

    bool contained = aaa_string_equals(lhs, rhs);
    aaa_stack_push_bool(stack, contained);

    aaa_string_dec_ref(lhs);
    aaa_string_dec_ref(rhs);
}

void aaa_stack_str_join(struct aaa_stack *stack) {
    struct aaa_vector *parts = aaa_stack_pop_vec(stack);
    struct aaa_string *string = aaa_stack_pop_str(stack);

    struct aaa_string *joined = aaa_string_join(string, parts);
    aaa_stack_push_str(stack, joined);

    aaa_vector_dec_ref(parts);
    aaa_string_dec_ref(string);
}

void aaa_stack_str_len(struct aaa_stack *stack) {
    struct aaa_string *string = aaa_stack_pop_str(stack);

    size_t length = aaa_string_len(string);
    aaa_stack_push_int(stack, (int)length);

    aaa_string_dec_ref(string);
}

void aaa_stack_str_lower(struct aaa_stack *stack) {
    struct aaa_string *string = aaa_stack_pop_str(stack);

    struct aaa_string *lower = aaa_string_lower(string);
    aaa_stack_push_str(stack, lower);

    aaa_string_dec_ref(string);
}

void aaa_stack_str_upper(struct aaa_stack *stack) {
    struct aaa_string *string = aaa_stack_pop_str(stack);

    struct aaa_string *upper = aaa_string_upper(string);
    aaa_stack_push_str(stack, upper);

    aaa_string_dec_ref(string);
}

void aaa_stack_str_replace(struct aaa_stack *stack) {
    struct aaa_string *replace = aaa_stack_pop_str(stack);
    struct aaa_string *search = aaa_stack_pop_str(stack);
    struct aaa_string *string = aaa_stack_pop_str(stack);

    struct aaa_string *replaced = aaa_string_replace(string, search, replace);
    aaa_stack_push_str(stack, replaced);

    aaa_string_dec_ref(replace);
    aaa_string_dec_ref(search);
    aaa_string_dec_ref(string);
}

void aaa_stack_str_split(struct aaa_stack *stack) {
    struct aaa_string *sep = aaa_stack_pop_str(stack);
    struct aaa_string *string = aaa_stack_pop_str(stack);

    struct aaa_vector *split = aaa_string_split(string, sep);
    aaa_stack_push_vec(stack, split);

    aaa_string_dec_ref(sep);
    aaa_string_dec_ref(string);
}

void aaa_stack_str_strip(struct aaa_stack *stack) {
    struct aaa_string *string = aaa_stack_pop_str(stack);

    struct aaa_string *stripped = aaa_string_strip(string);
    aaa_stack_push_str(stack, stripped);

    aaa_string_dec_ref(string);
}

void aaa_stack_str_find_after(struct aaa_stack *stack) {
    int start = aaa_stack_pop_int(stack);
    struct aaa_string *search = aaa_stack_pop_str(stack);
    struct aaa_string *string = aaa_stack_pop_str(stack);

    size_t offset;
    bool success;
    aaa_string_find_after(string, search, (size_t)start, &offset, &success);
    aaa_stack_push_int(stack, (int)offset);
    aaa_stack_push_bool(stack, success);

    aaa_string_dec_ref(search);
    aaa_string_dec_ref(string);
}

void aaa_stack_str_find(struct aaa_stack *stack) {
    struct aaa_string *search = aaa_stack_pop_str(stack);
    struct aaa_string *string = aaa_stack_pop_str(stack);

    bool success;
    size_t offset;
    aaa_string_find(string, search, &offset, &success);
    aaa_stack_push_int(stack, (int)offset);
    aaa_stack_push_bool(stack, success);

    aaa_string_dec_ref(search);
    aaa_string_dec_ref(string);
}

void aaa_stack_str_substr(struct aaa_stack *stack) {
    int end = aaa_stack_pop_int(stack);
    int start = aaa_stack_pop_int(stack);
    struct aaa_string *string = aaa_stack_pop_str(stack);

    bool success;
    struct aaa_string *substr =
        aaa_string_substr(string, (size_t)start, (size_t)end, &success);
    aaa_stack_push_str(stack, substr);
    aaa_stack_push_bool(stack, success);

    aaa_string_dec_ref(string);
}

void aaa_stack_str_to_bool(struct aaa_stack *stack) {
    struct aaa_string *string = aaa_stack_pop_str(stack);

    bool boolean, success;
    aaa_string_to_bool(string, &boolean, &success);
    aaa_stack_push_bool(stack, boolean);
    aaa_stack_push_bool(stack, success);

    aaa_string_dec_ref(string);
}

void aaa_stack_str_to_int(struct aaa_stack *stack) {
    struct aaa_string *string = aaa_stack_pop_str(stack);

    bool success;
    int integer;
    aaa_string_to_int(string, &integer, &success);
    aaa_stack_push_int(stack, integer);
    aaa_stack_push_bool(stack, success);

    aaa_string_dec_ref(string);
}

void aaa_stack_vec_copy(struct aaa_stack *stack) {
    struct aaa_vector *vec = aaa_stack_pop_vec(stack);

    struct aaa_vector *copy = aaa_vector_copy(vec);
    aaa_stack_push_vec(stack, copy);

    aaa_vector_dec_ref(vec);
}

void aaa_stack_map_copy(struct aaa_stack *stack) {
    struct aaa_map *map = aaa_stack_pop_map(stack);

    struct aaa_map *copy = aaa_map_copy(map);
    aaa_stack_push_map(stack, copy);

    aaa_map_dec_ref(map);
}

void aaa_stack_field_query(struct aaa_stack *stack) {
    struct aaa_string *field_name = aaa_stack_pop_str(stack);
    struct aaa_struct *s = aaa_stack_pop_struct(stack);

    const char *field_name_raw = aaa_string_raw(field_name);
    struct aaa_variable *field = aaa_struct_get_field(s, field_name_raw);

    aaa_stack_push(stack, field);

    aaa_string_dec_ref(field_name);
    aaa_struct_dec_ref(s);
}

void aaa_stack_field_update(struct aaa_stack *stack) {
    struct aaa_variable *new_value = aaa_stack_pop(stack);
    struct aaa_string *field_name = aaa_stack_pop_str(stack);
    struct aaa_struct *s = aaa_stack_pop_struct(stack);

    const char *field_name_raw = aaa_string_raw(field_name);
    aaa_struct_set_field(s, field_name_raw, new_value);

    aaa_variable_dec_ref(new_value);
    aaa_string_dec_ref(field_name);
    aaa_struct_dec_ref(s);
}

void aaa_stack_fsync(struct aaa_stack *stack) {
    int fd = aaa_stack_pop_int(stack);

    if (fsync(fd) == -1) {
        aaa_stack_push_bool(stack, false);
    }

    aaa_stack_push_bool(stack, true);
}

void aaa_stack_environ(struct aaa_stack *stack) {
    struct aaa_map *map = aaa_map_new();

    struct aaa_string *splitter = aaa_string_new("=", false);

    for (char **env_item = environ; *env_item; env_item++) {
        struct aaa_string *item = aaa_string_new(*env_item, false);
        struct aaa_vector *split = aaa_string_split(item, splitter);

        struct aaa_variable *key = aaa_vector_get(split, 0);
        struct aaa_variable *value = aaa_vector_get(split, 1);

        aaa_map_set(map, key, value);

        aaa_string_dec_ref(item);
        aaa_vector_dec_ref(split);
    }

    aaa_stack_push_map(stack, map);
}

void aaa_stack_execve(struct aaa_stack *stack) {
    struct aaa_map *env_map = aaa_stack_pop_map(stack);
    struct aaa_vector *argv_vec = aaa_stack_pop_vec(stack);
    struct aaa_string *path_str = aaa_stack_pop_str(stack);

    size_t argv_length = aaa_vector_size(argv_vec);
    size_t env_length = aaa_map_size(env_map);

    const char *path = aaa_string_raw(path_str);
    char **argv = malloc((argv_length + 1) * sizeof(*argv));

    for (size_t i = 0; i < argv_length; i++) {
        struct aaa_variable *argv_item_var = aaa_vector_get(argv_vec, i);
        struct aaa_string *argv_item = aaa_variable_get_str(argv_item_var);

        const char *argv_item_raw = aaa_string_raw(argv_item);
        size_t argv_item_length = aaa_string_len(argv_item);

        argv[i] = malloc((argv_item_length + 1) * sizeof(char));
        strcpy(argv[i], argv_item_raw);
    }
    argv[argv_length] = NULL;

    char **env = malloc((env_length + 1) * sizeof(*env));

    struct aaa_map_iter *env_iter = aaa_map_iter_new(env_map);

    struct aaa_variable *env_key_var = NULL;
    struct aaa_variable *env_value_var = NULL;

    size_t env_offset = 0;
    while (aaa_map_iter_next(env_iter, &env_key_var, &env_value_var)) {
        struct aaa_string *env_key = aaa_variable_get_str(env_key_var);
        struct aaa_string *env_value = aaa_variable_get_str(env_value_var);

        size_t key_length = aaa_string_len(env_key);
        size_t value_length = aaa_string_len(env_value);

        char *env_item = malloc(key_length + value_length + 2 * sizeof(char));
        sprintf(env_item, "%s=%s", aaa_string_raw(env_key),
                aaa_string_raw(env_value));

        env[env_offset] = env_item;
        env_offset++;
    }

    env[env_length] = NULL;

    execve(path, argv, env);

    // NOTE: if execve() succeeds, it doesn't return
    // It can only return an error.
    aaa_stack_push_bool(stack, false);
}

void aaa_stack_fork(struct aaa_stack *stack) {
    int pid = fork();

    aaa_stack_push_int(stack, pid);
}

void aaa_stack_waitpid(struct aaa_stack *stack) {
    int options = aaa_stack_pop_int(stack);
    int pid = aaa_stack_pop_int(stack);

    int changed_pid = waitpid(pid, NULL, options);

    if (changed_pid == 0) {
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_bool(stack, false);
    } else {
        aaa_stack_push_int(stack, changed_pid);
        aaa_stack_push_bool(stack, true);
    }
}

void aaa_stack_getcwd(struct aaa_stack *stack) {
    size_t buff_size = PATH_MAX;
    char *buff = malloc(buff_size);

    if (getcwd(buff, buff_size) == NULL) {
        fprintf(stderr, "getcwd() failed\n");
        abort();
    }

    aaa_stack_push_str_raw(stack, buff, true);
}

void aaa_stack_chdir(struct aaa_stack *stack) {
    struct aaa_string *path = aaa_stack_pop_str(stack);
    const char *path_raw = aaa_string_raw(path);

    if (chdir(path_raw) == 0) {
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_bool(stack, false);
    }

    aaa_string_dec_ref(path);
}

void aaa_stack_close(struct aaa_stack *stack) {
    int fd = aaa_stack_pop_int(stack);

    if (close(fd) == 0) {
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_bool(stack, false);
    }
}

void aaa_stack_getpid(struct aaa_stack *stack) {
    int pid = getpid();

    aaa_stack_push_int(stack, pid);
}

void aaa_stack_getppid(struct aaa_stack *stack) {
    int ppid = getppid();

    aaa_stack_push_int(stack, ppid);
}

void aaa_stack_getenv(struct aaa_stack *stack) {
    struct aaa_string *name = aaa_stack_pop_str(stack);
    const char *name_raw = aaa_string_raw(name);

    const char *value = getenv(name_raw);

    if (value) {
        aaa_stack_push_str_raw(stack, value, false);
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_str_raw(stack, "", false);
        aaa_stack_push_bool(stack, false);
    }

    aaa_string_dec_ref(name);
}

void aaa_stack_gettimeofday(struct aaa_stack *stack) {
    struct timeval tv;

    if (gettimeofday(&tv, NULL) != 0) {
        fprintf(stderr, "gettimeofday() failed\n");
        abort();
    }

    aaa_stack_push_int(stack, (int)tv.tv_sec);
    aaa_stack_push_int(stack, (int)tv.tv_usec);
}

void aaa_stack_open(struct aaa_stack *stack) {
    int mode = aaa_stack_pop_int(stack);
    int flags = aaa_stack_pop_int(stack);
    struct aaa_string *path = aaa_stack_pop_str(stack);

    const char *path_raw = aaa_string_raw(path);

    int fd = open(path_raw, flags, mode);

    if (fd == -1) {
        aaa_stack_push_int(stack, 0);
        aaa_stack_push_bool(stack, false);
    } else {
        aaa_stack_push_int(stack, fd);
        aaa_stack_push_bool(stack, true);
    }

    aaa_string_dec_ref(path);
}

void aaa_stack_setenv(struct aaa_stack *stack) {
    struct aaa_string *value = aaa_stack_pop_str(stack);
    struct aaa_string *name = aaa_stack_pop_str(stack);

    const char *value_raw = aaa_string_raw(value);
    const char *name_raw = aaa_string_raw(name);

    if (setenv(name_raw, value_raw, 1) == -1) {
        fprintf(stderr, "setenv() failed\n");
        abort();
    }

    aaa_string_dec_ref(value);
    aaa_string_dec_ref(name);
}

void aaa_stack_time(struct aaa_stack *stack) {
    time_t timestamp = time(NULL);

    aaa_stack_push_int(stack, (int)timestamp);
}

void aaa_stack_unlink(struct aaa_stack *stack) {
    struct aaa_string *path = aaa_stack_pop_str(stack);

    const char *path_raw = aaa_string_raw(path);

    if (unlink(path_raw) == 0) {
        aaa_stack_push_bool(stack, true);
    } else {
        aaa_stack_push_bool(stack, false);
    }

    aaa_string_dec_ref(path);
}

void aaa_stack_unsetenv(struct aaa_stack *stack) {
    struct aaa_string *name = aaa_stack_pop_str(stack);

    const char *name_raw = aaa_string_raw(name);

    if (unsetenv(name_raw) == -1) {
        fprintf(stderr, "unsetenv() failed\n");
        abort();
    }

    aaa_string_dec_ref(name);
}

#include "stack.h"

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <netdb.h>
#include <arpa/inet.h>

static void aaa_variable_check_kind(const struct aaa_variable *var, enum aaa_kind kind) {
    if (var->kind != kind) {
        fprintf(stderr, "Aaa type error\n");
        abort();
    }
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

static struct aaa_vector *aaa_stack_pop_vec(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    aaa_variable_check_kind(top, AAA_VECTOR);
    return top->vector;
}

static struct aaa_map *aaa_stack_pop_map(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_pop(stack);
    aaa_variable_check_kind(top, AAA_MAP);
    return top->map;
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


void aaa_stack_push_vec(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_push(stack);
    top->kind = AAA_VECTOR;
    top->vector = malloc(sizeof(*top->vector));
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


void aaa_stack_push_map(struct aaa_stack *stack) {
    struct aaa_variable *top = aaa_stack_push(stack);
    top->kind = AAA_MAP;
    top->map = malloc(sizeof(*top->map));
    aaa_map_init(top->map);
}

void aaa_stack_map_set(struct aaa_stack *stack) {
    struct aaa_variable *value = aaa_stack_pop(stack);
    struct aaa_variable *key = aaa_stack_pop(stack);
    struct aaa_map *map = aaa_stack_pop_map(stack);

    aaa_map_set(map, key, value);
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

    struct aaa_variable *top = aaa_stack_push(stack);
    *top = *value;
}

void aaa_stack_map_has_key(struct aaa_stack *stack) {
    struct aaa_variable *key = aaa_stack_pop(stack);
    struct aaa_map *map = aaa_stack_pop_map(stack);

    bool has_key = aaa_map_has_key(map, key);
    aaa_stack_push_bool(stack, has_key);
}

void aaa_stack_map_size(struct aaa_stack *stack) {
    struct aaa_map *map = aaa_stack_pop_map(stack);

    size_t size = aaa_map_size(map);
    aaa_stack_push_int(stack, size);
}

void aaa_stack_map_empty(struct aaa_stack *stack) {
    struct aaa_map *map = aaa_stack_pop_map(stack);

    bool is_empty = aaa_map_empty(map);
    aaa_stack_push_bool(stack, is_empty);
}

void aaa_stack_map_clear(struct aaa_stack *stack) {
    struct aaa_map *map = aaa_stack_pop_map(stack);

    aaa_map_clear(map);
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

    struct aaa_variable *top = aaa_stack_push(stack);
    *top = *value;
}

void aaa_stack_map_drop(struct aaa_stack *stack) {
    struct aaa_variable *key = aaa_stack_pop(stack);
    struct aaa_map *map = aaa_stack_pop_map(stack);

    aaa_map_drop(map, key);
}

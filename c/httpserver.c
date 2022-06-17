// compile: gcc -Wall -Wextra -g -o httpserver httpserver.c

// run: ./httpserver

// send request: curl -v http://localhost:5002/


#include <stdio.h>
#include <stdlib.h>

#include <netdb.h>
#include <netinet/in.h>

#include <unistd.h>
#include <string.h>

#define PORT 5002

int main() {

    // create socket
    int socket_fd = socket(AF_INET, SOCK_STREAM, 0);

    if (socket_fd < 0) {
        perror("ERROR opening socket");
        exit(1);
    }

    struct sockaddr_in server_socket = (struct sockaddr_in) {
        .sin_family = AF_INET,
        .sin_addr.s_addr = INADDR_ANY,
        .sin_port = htons(PORT),
    };

    // bind socket to host (0.0.0.0) and port (PORT)
    if (bind(socket_fd, (struct sockaddr *) &server_socket, sizeof(server_socket)) < 0) {
        perror("ERROR on binding");
        exit(1);
    }

    // tell socket to accept incoming connections
    if (listen(socket_fd, 5) < 0) {
        perror("ERROR on listening");
        exit(1);
    }

    printf("Listening on port %d\n", PORT);

    struct sockaddr_in client_socket;
    unsigned client_socket_length = sizeof(client_socket);
    char request_buffer[256];

    while (1) {
        int accept_fd = accept(socket_fd, (struct sockaddr *) &client_socket, &client_socket_length);

        if (accept_fd < 0) {
            perror("ERROR on accept");
            exit(1);
        }

        memset(request_buffer, 0, 256);

        // read request
        int len_read = read(accept_fd, request_buffer, 255);

        if (len_read < 0) {
            perror("ERROR reading from socket");
            exit(1);
        }

        printf("Got request: %s\n", request_buffer);

        const char *response =
        (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Content-Length: 27\r\n"
            "\r\n"
            "{\"message\": \"Hello world!\"}"
        );

        // send respone to client
        int written = write(accept_fd, response, strlen(response));

        if (written < 0) {
            perror("ERROR writing to socket");
            exit(1);
        }

        close(accept_fd);
    }

    shutdown(socket_fd, SHUT_RDWR);

    return 0;
}

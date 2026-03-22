/* NeuroRift v2 — raw_socket.c: Raw socket creation and management */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

typedef struct {
    int fd;
    int error_code;
    char error_msg[256];
} RawSocket;

RawSocket create_raw_socket(int protocol) {
    RawSocket rs = {0};
    rs.fd = socket(AF_INET, SOCK_RAW, protocol);
    if (rs.fd < 0) {
        rs.error_code = errno;
        snprintf(rs.error_msg, sizeof(rs.error_msg),
                 "socket() failed: %s (requires CAP_NET_RAW)", strerror(errno));
    }
    return rs;
}

void close_raw_socket(RawSocket *rs) {
    if (rs && rs->fd >= 0) {
        close(rs->fd);
        rs->fd = -1;
    }
}

int main(int argc, char *argv[]) {
    /* Quick smoke test: open and close a raw socket, output JSON result */
    RawSocket rs = create_raw_socket(IPPROTO_TCP);
    if (rs.fd < 0) {
        printf("{\"status\": \"error\", \"message\": \"%s\"}\n", rs.error_msg);
        return 1;
    }
    close_raw_socket(&rs);
    printf("{\"status\": \"ok\", \"message\": \"Raw socket created successfully\"}\n");
    return 0;
}

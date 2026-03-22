/* NeuroRift v2 — tcp_probe.c: Low-level TCP port state detection */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>

/* Connect-based TCP probe with timeout — determines port state */
int tcp_probe(const char *host, int port, int timeout_ms) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return -1;

    /* Set non-blocking */
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port   = htons((uint16_t)port);
    inet_pton(AF_INET, host, &addr.sin_addr);

    int ret = connect(sock, (struct sockaddr *)&addr, sizeof(addr));
    int state = 0; /* 0=filtered, 1=open, 2=closed */

    if (ret == 0) {
        state = 1; /* connected immediately */
    } else if (errno == EINPROGRESS) {
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(sock, &fds);
        struct timeval tv = { timeout_ms / 1000, (timeout_ms % 1000) * 1000 };
        int sel = select(sock + 1, NULL, &fds, NULL, &tv);
        if (sel > 0) {
            int so_error;
            socklen_t len = sizeof(so_error);
            getsockopt(sock, SOL_SOCKET, SO_ERROR, &so_error, &len);
            state = (so_error == 0) ? 1 : 2; /* ECONNREFUSED = closed */
        }
    } else {
        state = 2;
    }

    close(sock);
    return state;
}

int main(int argc, char *argv[]) {
    char host[256] = "127.0.0.1";
    int  port = 80;
    int  timeout_ms = 2000;

    for (int i = 1; i < argc - 1; i++) {
        if (strcmp(argv[i], "--target")  == 0) snprintf(host, sizeof(host), "%s", argv[++i]);
        if (strcmp(argv[i], "--port")    == 0) port       = atoi(argv[++i]);
        if (strcmp(argv[i], "--timeout") == 0) timeout_ms = atoi(argv[++i]);
    }

    int state = tcp_probe(host, port, timeout_ms);
    const char *state_str = state == 1 ? "open" : state == 2 ? "closed" : "filtered";

    printf("{\"host\": \"%s\", \"port\": %d, \"state\": \"%s\"}\n",
           host, port, state_str);
    return 0;
}

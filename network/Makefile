CC = gcc
CFLAGS = -O2 -Wall -Wextra

all: raw_socket packet_crafter tcp_probe

raw_socket: raw_socket.c
	$(CC) $(CFLAGS) -o raw_socket raw_socket.c

packet_crafter: packet_crafter.c
	$(CC) $(CFLAGS) -o packet_crafter packet_crafter.c

tcp_probe: tcp_probe.c
	$(CC) $(CFLAGS) -o tcp_probe tcp_probe.c

clean:
	rm -f raw_socket packet_crafter tcp_probe

.PHONY: all clean

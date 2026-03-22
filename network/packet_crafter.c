/* NeuroRift v2 — packet_crafter.c: Custom TCP/IP packet construction */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

/* Pseudo header for TCP checksum calculation */
struct pseudo_header {
    u_int32_t source_address;
    u_int32_t dest_address;
    u_int8_t  placeholder;
    u_int8_t  protocol;
    u_int16_t tcp_length;
};

/* RFC 1071 checksum */
unsigned short checksum(void *b, int len) {
    unsigned short *buf = b;
    unsigned int sum = 0;
    unsigned short result;
    for (sum = 0; len > 1; len -= 2)
        sum += *buf++;
    if (len == 1)
        sum += *(unsigned char *)buf;
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    result = ~sum;
    return result;
}

/* Craft a TCP SYN packet.
 * Args (from CLI): --src-ip <ip> --dst-ip <ip> --dst-port <port> --ttl <n>
 * Output: JSON result
 */
int main(int argc, char *argv[]) {
    char src_ip[64] = "127.0.0.1";
    char dst_ip[64] = "127.0.0.1";
    int  dst_port    = 80;
    int  ttl         = 64;

    for (int i = 1; i < argc - 1; i++) {
        if (strcmp(argv[i], "--src-ip")   == 0) snprintf(src_ip, sizeof(src_ip), "%s", argv[++i]);
        if (strcmp(argv[i], "--dst-ip")   == 0) snprintf(dst_ip, sizeof(dst_ip), "%s", argv[++i]);
        if (strcmp(argv[i], "--dst-port") == 0) dst_port = atoi(argv[++i]);
        if (strcmp(argv[i], "--ttl")      == 0) ttl      = atoi(argv[++i]);
    }

    /* Build packet buffer */
    char packet[4096];
    memset(packet, 0, sizeof(packet));

    struct iphdr  *iph  = (struct iphdr *)packet;
    struct tcphdr *tcph = (struct tcphdr *)(packet + sizeof(struct iphdr));

    /* IP header */
    iph->ihl      = 5;
    iph->version  = 4;
    iph->tos      = 0;
    iph->tot_len  = sizeof(struct iphdr) + sizeof(struct tcphdr);
    iph->id       = htons(54321);
    iph->frag_off = 0;
    iph->ttl      = (uint8_t)ttl;
    iph->protocol = IPPROTO_TCP;
    iph->check    = 0;
    iph->saddr    = inet_addr(src_ip);
    iph->daddr    = inet_addr(dst_ip);
    iph->check    = checksum((unsigned short *)packet, iph->tot_len);

    /* TCP SYN header */
    tcph->source  = htons(12345);
    tcph->dest    = htons((uint16_t)dst_port);
    tcph->seq     = 0;
    tcph->ack_seq = 0;
    tcph->doff    = 5;
    tcph->syn     = 1;
    tcph->window  = htons(65535);
    tcph->check   = 0;
    tcph->urg_ptr = 0;

    /* TCP checksum using pseudo header */
    struct pseudo_header ph;
    ph.source_address = inet_addr(src_ip);
    ph.dest_address   = inet_addr(dst_ip);
    ph.placeholder    = 0;
    ph.protocol       = IPPROTO_TCP;
    ph.tcp_length     = htons(sizeof(struct tcphdr));

    char psh[512];
    memcpy(psh, &ph, sizeof(struct pseudo_header));
    memcpy(psh + sizeof(struct pseudo_header), tcph, sizeof(struct tcphdr));
    tcph->check = checksum((unsigned short *)psh,
                           sizeof(struct pseudo_header) + sizeof(struct tcphdr));

    printf("{\"status\": \"crafted\", \"src\": \"%s\", \"dst\": \"%s\", "
           "\"port\": %d, \"ttl\": %d, \"packet_size\": %lu}\n",
           src_ip, dst_ip, dst_port, ttl,
           sizeof(struct iphdr) + sizeof(struct tcphdr));

    return 0;
}

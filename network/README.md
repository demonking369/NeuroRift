# NeuroRift Network C Binaries

These binaries are compiled for maximum performance. Due to their low-level network operations, some of them require elevated privileges.

### Requirements
- A modern Linux environment (e.g., Kali Linux)
- Standard build tools (`gcc`, `make`)

### Binaries

1. **`raw_socket`**
   - **Requires**: `sudo` (or `CAP_NET_RAW` capability)
   - Usage: `./raw_socket`
   - Description: Attempts to create a raw TCP socket (`IPPROTO_TCP`). Fails hard if running as an unprivileged user. Used for basic capabilities verification by the AI loop.

2. **`packet_crafter`**
   - **Requires**: Standard user
   - Usage: `./packet_crafter --src-ip <ip> --dst-ip <ip> --dst-port <port> --ttl <n>`
   - Description: Generates a complete TCP SYN packet payload, fully calculating IP and TCP checksums dynamically (RFC-1071 standard).

3. **`tcp_probe`**
   - **Requires**: Standard user 
   - Usage: `./tcp_probe --target <ip> --port <port> --timeout <ms>`
   - Description: Non-blocking fast socket connection attempting to precisely determine the target port state (`open`, `closed`, `filtered`).

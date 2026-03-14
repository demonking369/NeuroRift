# OpenClaw (NeuroRift Rust Core) — Dockerfile
# Multi-stage build: compiles the Rust binary in stage 1,
# copies only the binary into a minimal Debian runtime in stage 2.

# ─────────── Stage 1: Build ───────────
FROM rust:1.83-slim AS builder

# System deps for Rust compilation (OpenSSL, pkg-config)
RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
# Copy workspace manifests first for layer caching
COPY core/Cargo.toml core/Cargo.lock ./
COPY core/neurorift-core/Cargo.toml ./neurorift-core/

# Dummy source to pre-cache dependencies
RUN mkdir -p neurorift-core/src \
    && echo "fn main() {}" > neurorift-core/src/main.rs \
    && echo "pub fn lib() {}" > neurorift-core/src/lib.rs
RUN cargo build --release --manifest-path neurorift-core/Cargo.toml 2>/dev/null || true
# Remove dummy artifacts so real source triggers a rebuild
RUN rm -rf neurorift-core/src

# Copy real source
COPY core/neurorift-core/src ./neurorift-core/src

# Build release binary
RUN cargo build --release --manifest-path neurorift-core/Cargo.toml

# ─────────── Stage 2: Runtime ───────────
FROM debian:bookworm-slim AS runtime

# curl is required for the entrypoint health-wait loop and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy compiled binary from builder
COPY --from=builder /build/target/release/neurorift-core /app/neurorift-core

# Copy entrypoint
COPY docker/openclaw/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Data directory (mounted as volume at runtime)
ENV NEURORIFT_HOME=/data/neurorift
RUN mkdir -p /data/neurorift

# WebSocket server port
EXPOSE 8765

# Health check — TCP connectivity on the WebSocket port
HEALTHCHECK --interval=10s --timeout=5s --start-period=40s --retries=5 \
    CMD curl -sf http://localhost:8765/health 2>/dev/null || \
    (echo >/dev/tcp/localhost/8765) 2>/dev/null || exit 1

ENTRYPOINT ["/entrypoint.sh"]

# NeuroRift Web UI — Dockerfile
# Multi-stage build: compiles Next.js in stage 1, serves standalone output in stage 2.

# ─────────── Stage 1: Build ───────────
FROM node:20-alpine AS builder

# Required for native addons
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy manifests first for layer caching
COPY web-ui/package.json web-ui/package-lock.json* ./
RUN npm ci --prefer-offline

# Copy full source and build
COPY web-ui/ ./

# Inject public env vars at build time (Next.js rewrites use server-side vars)
ARG NEURORIFT_BRIDGE_URL=http://neurorift:8766
ARG OPENCLAW_WS_URL=http://openclaw:8765
ENV NEURORIFT_BRIDGE_URL=$NEURORIFT_BRIDGE_URL
ENV OPENCLAW_WS_URL=$OPENCLAW_WS_URL

# Ensure public/ exists so the runtime COPY never fails on projects without one
RUN mkdir -p public && npm run build

# ─────────── Stage 2: Runtime ───────────
FROM node:20-alpine AS runtime

RUN apk add --no-cache wget

WORKDIR /app

ENV NODE_ENV=production
# next.config.js output: 'standalone' generates a self-contained server
# Copy the standalone bundle, static assets, and public files
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME=0.0.0.0

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD wget -qO- http://localhost:3000 || exit 1

CMD ["node", "server.js"]

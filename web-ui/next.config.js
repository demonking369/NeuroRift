/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    reactStrictMode: true,

    // When running in Docker Compose the Next.js container proxies
    // API calls internally so the browser never directly talks to
    // backend services. The env vars are injected by docker-compose.yml.
    async rewrites() {
        const bridgeUrl = process.env.NEURORIFT_BRIDGE_URL || 'http://localhost:8766';
        const openclawWs = process.env.OPENCLAW_WS_URL || 'http://localhost:8765';
        return [
            {
                source: '/api/bridge/:path*',
                destination: `${bridgeUrl}/:path*`,
            },
            {
                source: '/api/ws/:path*',
                destination: `${openclawWs}/:path*`,
            },
        ];
    },
}

module.exports = nextConfig

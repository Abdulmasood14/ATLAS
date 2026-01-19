/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  env: {
    // In production, we use relative paths via Next.js rewrites
    NEXT_PUBLIC_API_URL: process.env.NODE_ENV === 'production' ? '' : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'),
    NEXT_PUBLIC_WS_URL: process.env.NODE_ENV === 'production' ? '' : (process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'),
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/health',
        destination: 'http://localhost:8000/health',
      },
    ]
  },
}

module.exports = nextConfig

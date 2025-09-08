/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    // Only proxy to local FastAPI when NEXT_PUBLIC_USE_LOCAL_API is 'true'
    if (process.env.NEXT_PUBLIC_USE_LOCAL_API === 'true') {
      return [
        { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' },
      ]
    }
    // In production, if NEXT_PUBLIC_API_BASE is set, forward certain API routes to FastAPI
    const apiBase = process.env.NEXT_PUBLIC_API_BASE
    if (apiBase && apiBase.startsWith('http')) {
      return [
        { source: '/api/vorp', destination: `${apiBase}/api/vorp` },
        { source: '/api/vorp_gaps', destination: `${apiBase}/api/vorp_gaps` },
        { source: '/api/rankings', destination: `${apiBase}/api/rankings` },
      ]
    }
    return []
  },
}

export default nextConfig

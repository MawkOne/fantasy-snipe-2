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
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ]
    }
    return []
  },
}

export default nextConfig

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allows CI/agents to build without clobbering an active local dev server.
  distDir: process.env.NEXT_DIST_DIR || ".next",
};
module.exports = nextConfig;
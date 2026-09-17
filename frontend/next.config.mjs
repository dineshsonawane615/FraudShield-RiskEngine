/** @type {import('next').NextConfig} */
const nextConfig = {
  // NOTE: Do NOT add typescript.ignoreBuildErrors — TypeScript errors should
  // fail the build so bugs are caught before deployment.
  images: {
    unoptimized: true,
  },
}

export default nextConfig

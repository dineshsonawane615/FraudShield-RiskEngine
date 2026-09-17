/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  // NOTE: Do NOT add typescript.ignoreBuildErrors — TypeScript errors should
  // fail the build so bugs are caught before deployment.
  images: {
    unoptimized: true,
  },
}

export default nextConfig

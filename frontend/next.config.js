/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 后端 API 代理
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;

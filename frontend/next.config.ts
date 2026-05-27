import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker 배포용 standalone 출력 (node server.js로 실행 가능한 최소 번들)
  output: "standalone",

  // 백엔드 API URL을 환경 변수로 관리
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  },
  // 백엔드 API 프록시 (개발 편의)
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
      {
        source: "/feed.xml",
        destination: `${apiUrl}/api/feed.xml`,
      },
    ];
  },
};

export default nextConfig;

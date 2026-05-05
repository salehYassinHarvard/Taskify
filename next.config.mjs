/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "lh3.googleusercontent.com" },
      { protocol: "https", hostname: "*.supabase.co" },
    ],
  },
  async rewrites() {
    // Local dev: forward /api/* to the Python FastAPI server on :8000.
    // On Vercel, /api/* is served by the serverless function directly (no rewrite needed).
    if (process.env.NODE_ENV === "development" && process.env.PYTHON_API_URL) {
      return [
        {
          source: "/api/:path*",
          destination: `${process.env.PYTHON_API_URL}/api/:path*`,
        },
      ];
    }
    return [];
  },
};

export default nextConfig;

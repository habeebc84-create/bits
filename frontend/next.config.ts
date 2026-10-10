import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // NOT static export: /research/[id] and /discoveries/[id] are dynamic routes.
  // Netlify's Next.js Runtime handles SSR → Functions automatically (see netlify.toml).
  env: { NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000" },
};
export default nextConfig;

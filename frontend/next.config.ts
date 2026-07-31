import type { NextConfig } from "next";
import path from "path";
import { fileURLToPath } from "url";

const root = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  // Pin Turbopack root to frontend/ so monorepo lockfiles don't widen the proxy bundle.
  turbopack: {
    root,
  },
};

export default nextConfig;

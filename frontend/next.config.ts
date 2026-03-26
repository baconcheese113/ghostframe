import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // igv.esm.js accesses `document` at module load time, which causes Turbopack
  // to fail during server-side module evaluation. Marking it as a server
  // external package prevents bundling it for SSR entirely; the dynamic
  // import('igv') in useEffect runs only in the browser where DOM is available.
  serverExternalPackages: ['igv'],
};

export default nextConfig;

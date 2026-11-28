import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // The dictionary is read at request time (e.g. home pagination) from a configurable path.
  outputFileTracingIncludes: {
    "/*": ["data/dictionary.json", "data/fixtures/*.json", "data/duolingo/palabras.json"],
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;

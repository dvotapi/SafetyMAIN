import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const root = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    css: true,
  },
  resolve: {
    alias: {
      "@/app": path.join(root, "src/app"),
      "@/features": path.join(root, "src/features"),
      "@/components": path.join(root, "src/components"),
      "@/layouts": path.join(root, "src/layouts"),
      "@/lib": path.join(root, "src/lib"),
      "@/services": path.join(root, "src/services"),
      "@/hooks": path.join(root, "src/hooks"),
      "@/theme": path.join(root, "src/theme"),
      "@/types": path.join(root, "src/types"),
      "@/utils": path.join(root, "src/utils"),
      "@/icons": path.join(root, "src/icons"),
      "@": path.join(root, "src"),
    },
  },
});

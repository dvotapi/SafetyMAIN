import type { StorybookConfig } from "@storybook/react-vite";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(fileURLToPath(import.meta.url));

const config: StorybookConfig = {
  stories: ["../src/**/*.stories.@(ts|tsx)"],
  addons: [
    "@storybook/addon-essentials",
    "@storybook/addon-a11y",
    "@storybook/addon-themes",
    "@storybook/addon-viewport",
    "@storybook/addon-links",
    "@storybook/addon-interactions",
  ],
  framework: {
    name: "@storybook/react-vite",
    options: {},
  },
  async viteFinal(config) {
    config.resolve = config.resolve ?? {};
    config.resolve.alias = {
      ...config.resolve.alias,
      "@/app": path.join(root, "../src/app"),
      "@/features": path.join(root, "../src/features"),
      "@/components": path.join(root, "../src/components"),
      "@/layouts": path.join(root, "../src/layouts"),
      "@/lib": path.join(root, "../src/lib"),
      "@/services": path.join(root, "../src/services"),
      "@/hooks": path.join(root, "../src/hooks"),
      "@/theme": path.join(root, "../src/theme"),
      "@/types": path.join(root, "../src/types"),
      "@/utils": path.join(root, "../src/utils"),
      "@/icons": path.join(root, "../src/icons"),
      "@": path.join(root, "../src"),
    };
    return config;
  },
};

export default config;

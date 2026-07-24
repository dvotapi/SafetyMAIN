import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

/** @type {import('eslint').Linter.Config[]} */
const config = [
  {
    ignores: [
      ".next/**",
      "coverage/**",
      "storybook-static/**",
      "playwright-report/**",
      "test-results/**",
      "public/mockServiceWorker.js",
      "src/theme/generated/**",
    ],
  },
  ...compat.extends(
    "next/core-web-vitals",
    "next/typescript",
    "plugin:jsx-a11y/recommended",
  ),
  {
    rules: {
      "import/no-restricted-paths": [
        "error",
        {
          zones: [
            {
              target: "./src/components",
              from: "./src/features",
              message: "Shared components must not import business features.",
            },
            {
              target: "./src/theme",
              from: "./src/features",
              message: "Theme must not import business features.",
            },
            {
              target: "./src/features",
              from: "./src/app",
              message: "Features must not import app route internals.",
            },
          ],
        },
      ],
    },
  },
];

export default config;

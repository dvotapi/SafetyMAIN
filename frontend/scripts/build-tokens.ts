/**
 * Deterministic design-token generator.
 * Canonical source: src/theme/tokens/tokens.json
 *
 * Usage:
 *   npm run tokens:build
 *   npm run tokens:check
 */
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const sourcePath = path.join(root, "src/theme/tokens/tokens.json");
const outDir = path.join(root, "src/theme/generated");
const checkOnly = process.argv.includes("--check");

interface TokenFile {
  meta: { prefix: string; source: string; version: string };
  primitive: {
    palette: Record<string, string | Record<string, string>>;
    font: Record<string, Record<string, string>>;
    space: Record<string, string>;
    size: Record<string, Record<string, string>>;
    radius: Record<string, string>;
    shadow: Record<string, string>;
    z: Record<string, string>;
    motion: Record<string, string>;
    breakpoint: Record<string, string>;
    layout: Record<string, string>;
  };
  semantic: {
    light: { color: Record<string, string> };
    dark: { color: Record<string, string> };
  };
}

function flatten(
  obj: Record<string, unknown>,
  prefix = "",
): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [key, value] of Object.entries(obj)) {
    const next = prefix ? `${prefix}-${key}` : key;
    if (value !== null && typeof value === "object" && !Array.isArray(value)) {
      Object.assign(out, flatten(value as Record<string, unknown>, next));
    } else if (typeof value === "string" || typeof value === "number") {
      out[next] = String(value);
    }
  }
  return out;
}

function resolveRefs(
  value: string,
  paletteFlat: Record<string, string>,
): string {
  const match = /^\{palette\.(.+)\}$/.exec(value);
  if (!match?.[1]) {
    return value;
  }
  const key = `palette-${match[1].replaceAll(".", "-")}`;
  const resolved = paletteFlat[key];
  if (!resolved) {
    throw new Error(`Unresolved palette reference: ${value}`);
  }
  return resolved;
}

function cssVar(prefix: string, name: string): string {
  return `--${prefix}-${name}`;
}

function buildCss(tokens: TokenFile): string {
  const prefix = tokens.meta.prefix;
  const paletteFlat = flatten({ palette: tokens.primitive.palette });
  const primitiveFlat = flatten({
    font: tokens.primitive.font,
    space: tokens.primitive.space,
    size: tokens.primitive.size,
    radius: tokens.primitive.radius,
    shadow: tokens.primitive.shadow,
    z: tokens.primitive.z,
    motion: tokens.primitive.motion,
    breakpoint: tokens.primitive.breakpoint,
    layout: tokens.primitive.layout,
  });

  const lightLines = Object.entries(tokens.semantic.light.color).map(
    ([k, v]) =>
      `  ${cssVar(prefix, `color-${k}`)}: ${resolveRefs(v, paletteFlat)};`,
  );
  const darkLines = Object.entries(tokens.semantic.dark.color).map(
    ([k, v]) =>
      `  ${cssVar(prefix, `color-${k}`)}: ${resolveRefs(v, paletteFlat)};`,
  );
  const primitiveLines = Object.entries(primitiveFlat).map(
    ([k, v]) => `  ${cssVar(prefix, k)}: ${v};`,
  );
  const paletteLines = Object.entries(paletteFlat).map(
    ([k, v]) => `  ${cssVar(prefix, k)}: ${v};`,
  );

  return [
    "/* AUTO-GENERATED FILE. DO NOT EDIT MANUALLY. */",
    `/* Source: ${tokens.meta.source} | version ${tokens.meta.version} */`,
    ":root {",
    ...paletteLines,
    ...primitiveLines,
    ...lightLines,
    "}",
    "",
    '[data-theme="dark"] {',
    ...darkLines,
    "}",
    "",
    "@media (prefers-color-scheme: dark) {",
    '  :root:not([data-theme="light"]) {',
    ...darkLines.map((l) => `  ${l}`),
    "  }",
    "}",
    "",
  ].join("\n");
}

function buildTs(tokens: TokenFile): string {
  const prefix = tokens.meta.prefix;
  const paletteFlat = flatten({ palette: tokens.primitive.palette });
  const light = Object.fromEntries(
    Object.entries(tokens.semantic.light.color).map(([k, v]) => [
      k,
      resolveRefs(v, paletteFlat),
    ]),
  );
  const dark = Object.fromEntries(
    Object.entries(tokens.semantic.dark.color).map(([k, v]) => [
      k,
      resolveRefs(v, paletteFlat),
    ]),
  );

  const payload = {
    meta: tokens.meta,
    primitive: tokens.primitive,
    semantic: { light: { color: light }, dark: { color: dark } },
    cssVar: (name: string) => `var(--${prefix}-${name})`,
  };

  return [
    "/* AUTO-GENERATED FILE. DO NOT EDIT MANUALLY. */",
    `/* Source: ${tokens.meta.source} | version ${tokens.meta.version} */`,
    "",
    `export const tokens = ${JSON.stringify(payload, null, 2)} as const;`,
    "",
    "export type DesignTokens = typeof tokens;",
    "",
  ].join("\n");
}

function writeOrCheck(filePath: string, content: string): boolean {
  if (checkOnly) {
    if (!existsSync(filePath)) {
      console.error(`Missing generated file: ${filePath}`);
      return false;
    }
    const existing = readFileSync(filePath, "utf8");
    const a = createHash("sha256").update(existing).digest("hex");
    const b = createHash("sha256").update(content).digest("hex");
    if (a !== b) {
      console.error(`Stale generated file: ${filePath}`);
      return false;
    }
    return true;
  }
  mkdirSync(path.dirname(filePath), { recursive: true });
  writeFileSync(filePath, content, "utf8");
  return true;
}

const raw = readFileSync(sourcePath, "utf8");
const tokens = JSON.parse(raw) as TokenFile;
const css = buildCss(tokens);
const ts = buildTs(tokens);

const cssPath = path.join(outDir, "tokens.css");
const tsPath = path.join(outDir, "tokens.ts");
const okCss = writeOrCheck(cssPath, css);
const okTs = writeOrCheck(tsPath, ts);

if (checkOnly) {
  if (!okCss || !okTs) {
    process.exit(1);
  }
  console.log("Token outputs are up to date.");
} else {
  console.log(`Wrote ${path.relative(root, cssPath)}`);
  console.log(`Wrote ${path.relative(root, tsPath)}`);
}

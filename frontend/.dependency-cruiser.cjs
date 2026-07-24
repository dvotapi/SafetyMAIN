/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "components-no-features",
      severity: "error",
      comment: "Shared components must not import features.",
      from: { path: "^src/components" },
      to: { path: "^src/features" },
    },
    {
      name: "theme-no-features",
      severity: "error",
      comment: "Theme must not import features.",
      from: { path: "^src/theme" },
      to: { path: "^src/features" },
    },
    {
      name: "features-no-app",
      severity: "error",
      comment: "Features must not import app route internals.",
      from: { path: "^src/features" },
      to: { path: "^src/app" },
    },
    {
      name: "no-circular",
      severity: "warn",
      from: {},
      to: { circular: true },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
    enhancedResolveOptions: {
      exportsFields: ["exports"],
      conditionNames: ["import", "require", "node", "default"],
    },
  },
};

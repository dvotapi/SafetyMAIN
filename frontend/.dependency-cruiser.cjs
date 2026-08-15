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
      name: "hazard-api-no-components",
      severity: "error",
      comment: "Hazard API modules must not import React components.",
      from: { path: "^src/features/hazards/api" },
      to: {
        path: "^src/components|^src/features/hazards/components|^src/features/hazards/pages",
      },
    },
    {
      name: "risk-assessment-api-no-components",
      severity: "error",
      comment: "Risk Assessment API modules must not import React components.",
      from: { path: "^src/features/risk-assessments/api" },
      to: {
        path: "^src/components|^src/features/risk-assessments/components|^src/features/risk-assessments/pages",
      },
    },
    {
      name: "features-no-cross-feature-internals",
      severity: "error",
      comment: "Features must not import another feature's internals.",
      from: { path: "^src/features/([^/]+)" },
      to: {
        path: "^src/features/(?!\\1)([^/]+)/",
        pathNot: "^src/features/[^/]+/index\\.(ts|tsx)$",
      },
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

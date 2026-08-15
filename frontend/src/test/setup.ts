process.env.NEXT_PUBLIC_APP_URL ??= "http://localhost:3100";
process.env.NEXT_PUBLIC_API_BASE_URL ??= "http://localhost:8000";
process.env.NEXT_PUBLIC_APP_ENV ??= "test";

import "@testing-library/jest-dom/vitest";
import * as matchers from "vitest-axe/matchers";
import { expect } from "vitest";

expect.extend(matchers);

import "@/theme/generated/tokens.css";

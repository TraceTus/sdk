import { defineConfig } from "vitest/config";

/**
 * 100% coverage is the rule for this package, where the money and the
 * responsibility towards the network live: the thresholds make the suite fail
 * on the first uncovered line.
 */
export default defineConfig({
  test: {
    include: ["test/**/*.test.ts"],
    coverage: {
      enabled: true,
      provider: "v8",
      include: ["src/**"],
      reporter: ["text"],
      thresholds: { lines: 100, functions: 100, branches: 100, statements: 100 },
    },
  },
});

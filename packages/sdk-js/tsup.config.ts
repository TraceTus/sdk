/**
 * Build of `@tracetus/sdk`: ESM and CommonJS, with declarations.
 *
 * `@tracetus/core` is bundled in rather than depended on. It is our own pure
 * domain code — the Merkle rule the platform uses to build the proof is the one
 * that checks it — and bundling keeps the published package at **zero runtime
 * dependencies**, which is what lets a customer install one thing and have it
 * run on Node, in a browser, in a worker and on an edge runtime.
 */
import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts"],
  format: ["esm", "cjs"],
  outExtension: ({ format }) => ({ js: format === "cjs" ? ".cjs" : ".js" }),
  dts: true,
  /**
   * No source map in the package. A map built from a bundle embeds the sources
   * it was built from, and those include `@tracetus/core` and its own
   * dependency — our source, published to npm, for no one's benefit. The
   * published output is not minified, so a stack trace already points at
   * readable code.
   */
  sourcemap: false,
  clean: true,
  treeshake: true,
  /** Nothing is left external: the package ships with no dependencies at all. */
  noExternal: [/@tracetus\//, /@noble\//],
  target: "es2022",
});

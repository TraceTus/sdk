import { playwright } from "@vitest/browser-playwright";
import { type Plugin, defineConfig } from "vitest/config";

const REDIRECT_PREFIX = "/redirect-fixture";
const FOUND = 302;

/**
 * One path on the browser project's own server that answers a redirect.
 *
 * A browser does not hand `redirect: "manual"` the `30x`: it gives an opaque
 * response, status `0`, no headers. That cannot be built by hand — `Response`
 * refuses status `0` — so the only way to test what the client makes of it is
 * to have something actually redirect.
 */
function redirectFixture(): Plugin {
  return {
    name: "tracetus-redirect-fixture",
    configureServer(server) {
      server.middlewares.use(REDIRECT_PREFIX, (_request, response) => {
        response.statusCode = FOUND;
        response.setHeader("location", "https://elsewhere.test/v1/records");
        response.end();
      });
    },
  };
}

/**
 * Two projects, because two different things are being proved.
 *
 * **node** runs the suites that drive the client with a `fetch` of their own.
 *
 * **browser** runs one suite with **no** `fetch` injected, against a real
 * Chromium. That is the only way to catch a client that holds the global
 * `fetch` and calls it detached: Node allows it, a browser answers "Illegal
 * invocation", and so does an edge runtime. It imports the built bundle, so
 * what runs is what npm would publish — which means the build has to have run:
 * `pnpm test` goes through turbo, where `build` is declared as a dependency of
 * this package's `test`.
 */
export default defineConfig({
  test: {
    projects: [
      {
        test: {
          name: "node",
          include: ["test/**/*.test.ts"],
          exclude: ["test/browser/**"],
        },
      },
      {
        plugins: [redirectFixture()],
        test: {
          name: "browser",
          include: ["test/browser/**/*.test.ts"],
          browser: {
            enabled: true,
            headless: true,
            provider: playwright(),
            instances: [{ browser: "chromium" }],
          },
        },
      },
    ],
  },
});

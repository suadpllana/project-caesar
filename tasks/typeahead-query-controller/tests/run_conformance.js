/**
 * Conformance driver.
 *
 * Boots the agent's app with Vite, drives the real controller module through
 * a real browser, and writes a JSON verdict to stdout.
 *
 * Integrity: the agent's environment is mounted read-only for this run and
 * the harness/transport/types files are compared against the pristine copies
 * baked into this image. A submission that rewrites the test transport or the
 * harness to fake the invariants is rejected before any scenario runs.
 */

const { chromium } = require("playwright");
const { SCENARIOS, PRELUDE } = require("./scenarios");
const { createHash } = require("node:crypto");
const { readFileSync, existsSync } = require("node:fs");
const path = require("node:path");

const APP = process.env.APP_DIR || "/app";
const BASE = process.env.APP_URL || "http://127.0.0.1:5173/";

/**
 * Files the agent must not modify.
 *
 * The build configuration is included because Vite evaluates it as code: an
 * agent that can edit vite.config.ts (or package.json, which selects the
 * module system and can carry tool hooks) could execute arbitrary code inside
 * the verifier rather than solving the task. test.sh additionally serves the
 * image's own copies of these files, so this check is defence in depth
 * against the tampering rather than the only thing standing in its way.
 */
const PROTECTED = [
  "src/types.ts",
  "src/transport.ts",
  "src/main.ts",
  "vite.config.ts",
  "tsconfig.json",
  "package.json",
];

function sha(p) {
  return createHash("sha256").update(readFileSync(p)).digest("hex");
}

function checkIntegrity() {
  const violations = [];
  for (const rel of PROTECTED) {
    const live = path.join(APP, rel);
    const pristine = path.join("/tests/pristine", rel);
    if (!existsSync(live)) {
      violations.push(`${rel}: missing`);
      continue;
    }
    if (!existsSync(pristine)) continue;
    if (sha(live) !== sha(pristine)) {
      violations.push(`${rel}: modified`);
    }
  }
  return violations;
}

async function main() {
  const violations = checkIntegrity();
  if (violations.length > 0) {
    console.log(
      JSON.stringify({
        integrity: false,
        violations,
        results: [],
      }),
    );
    return;
  }

  const browser = await chromium.launch({
    args: ["--no-sandbox", "--disable-dev-shm-usage"],
  });
  const results = [];
  let pageErrors = [];

  try {
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    page.on("pageerror", (e) => pageErrors.push(String(e)));
    page.on("console", (m) => {
      if (m.type() === "error") pageErrors.push(m.text());
    });

    await page.goto(BASE, { waitUntil: "load", timeout: 60000 });

    // The module graph must have loaded and installed the harness.
    await page.waitForFunction(() => !!window.__harness, null, {
      timeout: 60000,
    });

    // A tick helper that flushes microtasks *and* a macrotask turn, so
    // promise chains inside the controller settle before we assert.
    await page.addInitScript(() => {});
    await page.evaluate(() => {
      window.tick = () =>
        new Promise((r) => setTimeout(r, 0)).then(
          () => new Promise((r) => setTimeout(r, 0)),
        );
    });

    for (const sc of SCENARIOS) {
      let verdict;
      try {
        verdict = await page.evaluate(
          `(async () => {
             const tick = window.tick;
             ${PRELUDE}
             try {
               ${sc.body}
             } catch (e) {
               if (e && e.name === "BadState") {
                 return { pass: false, detail: e.message };
               }
               throw e;
             }
           })()`,
        );
      } catch (err) {
        verdict = { pass: false, detail: `threw: ${String(err).slice(0, 300)}` };
      }
      results.push({
        id: sc.id,
        title: sc.title,
        pass: !!(verdict && verdict.pass),
        detail: (verdict && verdict.detail) || "no detail",
      });
    }
  } finally {
    await browser.close().catch(() => {});
  }

  console.log(
    JSON.stringify({ integrity: true, violations: [], results, pageErrors }),
  );
}

main().catch((e) => {
  console.log(
    JSON.stringify({
      integrity: true,
      violations: [],
      results: [],
      fatal: String(e),
    }),
  );
});

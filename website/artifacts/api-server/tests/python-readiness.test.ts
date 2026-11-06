import assert from "node:assert/strict";
import { test } from "node:test";
import { pythonReady, pythonUrl } from "../src/lib/python-service";

test("readiness requires real Python identity, successful status, and valid JSON", async () => {
  const original = globalThis.fetch;
  try {
    for (const [status, body, expected] of [
      [200, '{"status":"ok","service":"sada-evaluation-adapter"}', true],
      [503, '{"status":"ok","service":"sada-evaluation-adapter"}', false],
      [200, '{"status":"ok"}', false],
      [200, 'not json', false],
    ] as const) {
      globalThis.fetch = async () => new Response(body, { status });
      assert.equal(await pythonReady(), expected);
    }
    globalThis.fetch = async () => { throw new Error("connection refused"); };
    assert.equal(await pythonReady(), false);
    assert.match(pythonUrl("health"), /^http:\/\/127\.0\.0\.1:\d+\/api\/health$/);
  } finally {
    globalThis.fetch = original;
  }
});

test("hosted readiness keeps an eight-second abort budget", async () => {
  const originalFetch = globalThis.fetch;
  const originalTimeout = AbortSignal.timeout;
  const budgets: number[] = [];
  try {
    AbortSignal.timeout = (milliseconds: number) => {
      budgets.push(milliseconds);
      return new AbortController().signal;
    };
    globalThis.fetch = async (_url, init) => {
      assert.ok(init?.signal instanceof AbortSignal);
      return new Response('{"status":"ok","service":"sada-evaluation-adapter"}');
    };
    assert.equal(await pythonReady(), true);
    assert.deepEqual(budgets, [8_000]);
    globalThis.fetch = async () => { throw new DOMException("Deadline exceeded", "TimeoutError"); };
    assert.equal(await pythonReady(), false);
  } finally {
    globalThis.fetch = originalFetch;
    AbortSignal.timeout = originalTimeout;
  }
});

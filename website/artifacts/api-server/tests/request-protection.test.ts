import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import type { AddressInfo } from "node:net";
import express from "express";
import { createOriginProtection, createRequestProtection, requestErrorHandler } from "../src/lib/request-protection";

let clock = 0;
let entered = 0;
const releases: Array<() => void> = [];
const app = express();
app.set("trust proxy", "loopback");
app.use(createOriginProtection(["https://trusted.example"]));
app.use("/api/evaluations", ...createRequestProtection(() => clock));
app.post("/api/evaluations", async (req, res) => {
  entered++;
  if (req.body.hold) await new Promise<void>(resolve => releases.push(resolve));
  res.status(201).json({ id: "existing-contract", configuration: req.body, outputs: {} });
});
app.get("/api/evaluations/:id", (_req, res) => { res.json({ id: "preserved-id" }); });
app.use(requestErrorHandler);
const server = app.listen(0, "127.0.0.1");
let base: string;
before(async () => {
  if (!server.listening) await new Promise<void>(resolve => server.once("listening", resolve));
  base = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
});
after(async () => {
  for (const release of releases.splice(0)) release();
  server.closeAllConnections();
  await new Promise<void>(resolve => server.close(() => resolve()));
});
const post = (body = "{}", headers: Record<string, string> = {}) =>
  fetch(`${base}/api/evaluations`, { method: "POST", body,
    headers: { "Content-Type": "application/json", ...headers } });
function newWindow() { clock += 60_001; }
async function waitUntil(condition: () => boolean) {
  for (let i = 0; i < 100 && !condition(); i++) {
    await new Promise(resolve => setTimeout(resolve, 10));
  }
  assert.ok(condition(), "Timed out waiting for request admission");
}

test("six submissions per client, seventh 429; window and other clients recover", async () => {
  newWindow();
  for (let i = 0; i < 6; i++) assert.equal((await post()).status, 201);
  const limited = await post();
  assert.equal(limited.status, 429);
  assert.equal(limited.headers.get("retry-after"), "60");
  assert.equal(limited.headers.get("cache-control"), "no-store");
  assert.equal((await post("{}", { "X-Forwarded-For": "198.51.100.2" })).status, 201);
  newWindow();
  assert.equal((await post()).status, 201);
});

test("reads are independently limited to 120 and have no effect on saved IDs", async () => {
  newWindow();
  for (let i = 0; i < 120; i++) {
    const response = await fetch(`${base}/api/evaluations/preserved-id`);
    assert.equal(response.status, 200);
  }
  assert.equal((await fetch(`${base}/api/evaluations/preserved-id`)).status, 429);
  assert.equal((await post()).status, 201);
  newWindow();
  const restored = await fetch(`${base}/api/evaluations/preserved-id`);
  assert.deepEqual(await restored.json(), { id: "preserved-id" });
});

test("admission is bounded to two in-flight submissions, no waiting queue", async () => {
  newWindow();
  const previous = entered;
  const first = post('{"hold":true}');
  const second = post('{"hold":true}');
  await waitUntil(() => entered === previous + 2);
  try {
    const rejected = await post();
    assert.equal(rejected.status, 503);
    assert.equal(rejected.headers.get("retry-after"), "2");
    assert.equal(entered, previous + 2);
  } finally {
    for (const release of releases.splice(0)) release();
  }
  assert.equal((await first).status, 201);
  assert.equal((await second).status, 201);
  assert.equal((await post()).status, 201);
});

test("strict JSON, 4 KiB body limit, no decompression or URL-encoded forms", async () => {
  newWindow();
  const original = entered;
  for (const encoding of ["gzip", "br", "deflate"]) {
    assert.equal((await post("garbage", { "Content-Encoding": encoding })).status, 415);
  }
  assert.equal((await post("{}", { "Content-Type": "text/plain" })).status, 415);
  assert.equal((await post("stage=T+04", { "Content-Type": "application/x-www-form-urlencoded" })).status, 415);
  assert.equal((await post(" ".repeat(4097))).status, 413);
  assert.equal(entered, original);
  newWindow();
  const malformed = await post('{"private":"broken');
  assert.equal(malformed.status, 400);
  assert.deepEqual(await malformed.json(), { detail: "Invalid JSON request." });
  assert.equal((await post("{}", { "Content-Type": "application/json; charset=invalid" })).status, 415);
  assert.equal((await post("{}", { "Content-Encoding": "identity" })).status, 201);
});

test("CORS denies hostile origins, allows same-origin, and explicit trusted origins only", async () => {
  newWindow();
  for (const origin of ["https://hostile.example", "null"]) {
    const rejected = await post("{}", { Origin: origin });
    assert.equal(rejected.status, 403);
    assert.equal(rejected.headers.get("access-control-allow-origin"), null);
  }
  const sameOrigin = await post("{}", { Origin: base });
  assert.equal(sameOrigin.status, 201);
  assert.equal(sameOrigin.headers.get("access-control-allow-origin"), null);
  const trusted = await fetch(`${base}/api/evaluations`, {
    method: "OPTIONS",
    headers: { Origin: "https://trusted.example", "Access-Control-Request-Method": "POST" },
  });
  assert.equal(trusted.status, 204);
  assert.equal(trusted.headers.get("access-control-allow-origin"), "https://trusted.example");
  assert.throws(() => createOriginProtection(["*"]));
});

test("counter storage is bounded, does not evict active client limits, and expires", async () => {
  newWindow();
  for (let i = 0; i < 1_000; i++) {
    const response = await fetch(`${base}/api/evaluations/id`, {
      headers: { "X-Forwarded-For": `198.18.${Math.floor(i / 256)}.${i % 256}` },
    });
    assert.equal(response.status, 200);
  }
  assert.equal((await post()).status, 503);
  newWindow();
  assert.equal((await post()).status, 201);
});

test("forwarded IPs are ignored when the socket peer is not trusted", async () => {
  const untrustedApp = express();
  untrustedApp.use(...createRequestProtection());
  untrustedApp.post("/", (_req, res) => { res.status(201).json({}); });
  const untrustedServer = untrustedApp.listen(0, "127.0.0.1");
  await new Promise<void>(resolve => untrustedServer.once("listening", resolve));
  const url = `http://127.0.0.1:${(untrustedServer.address() as AddressInfo).port}/`;
  try {
    for (let i = 0; i < 7; i++) {
      const response = await fetch(url, { method: "POST", body: "{}",
        headers: { "Content-Type": "application/json", "X-Forwarded-For": `198.51.100.${i}` } });
      assert.equal(response.status, i === 6 ? 429 : 201);
    }
  } finally {
    untrustedServer.closeAllConnections();
    await new Promise<void>(resolve => untrustedServer.close(() => resolve()));
  }
});

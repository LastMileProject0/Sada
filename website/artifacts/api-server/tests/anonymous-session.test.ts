import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import type { AddressInfo } from "node:net";
import express from "express";
import { ANONYMOUS_COOKIE, SESSION_SECONDS, createAnonymousSession } from "../src/lib/anonymous-session";
import { createOriginProtection, createRequestProtection, requestErrorHandler } from "../src/lib/request-protection";

const secret = "test-only-key-not-a-production-credential-123456";
let clock = Date.now();
const app = express();
app.use(createOriginProtection());
app.use(...createRequestProtection(() => clock));
app.use(createAnonymousSession(secret, () => clock));
// Test-only response exposes the derived hash to assertions, never the credential.
app.post("/", (_req, res) => { res.status(201).json({ owner: res.locals.evaluationOwnerHash }); });
app.get("/", (_req, res) => { res.json({ owner: res.locals.evaluationOwnerHash }); });
app.use(requestErrorHandler);
const server = app.listen(0, "127.0.0.1");
let base: string;
before(async () => {
  if (!server.listening) await new Promise<void>(resolve => server.once("listening", resolve));
  base = `http://127.0.0.1:${(server.address() as AddressInfo).port}/`;
});
after(async () => {
  server.closeAllConnections();
  await new Promise<void>(resolve => server.close(() => resolve()));
});
const post = (cookie?: string, headers: Record<string, string> = {}) =>
  fetch(base, { method: "POST", headers: { "Content-Type": "application/json",
    Origin: new URL(base).origin,
    ...(cookie ? { Cookie: cookie } : {}), ...headers }, body: "{}" });
const cookieOf = (response: Response) => response.headers.get("set-cookie")!.split(";")[0]!;
const get = (cookie?: string) => fetch(base, {
  headers: cookie ? { Cookie: cookie } : {},
});

test("two new visitors get distinct unpredictable secure host-only credentials", async () => {
  const first = await post();
  const second = await post();
  assert.equal(first.status, 201);
  const attributes = first.headers.get("set-cookie")!;
  assert.match(attributes, /^__Host-sada-demo=/);
  for (const attribute of ["Secure", "HttpOnly", "SameSite=Lax", "Path=/", "Max-Age=86400"]) {
    assert.ok(attributes.includes(attribute));
  }
  assert.ok(!attributes.toLowerCase().includes("domain="));
  assert.notEqual(cookieOf(first), cookieOf(second));
  const a = await first.json();
  const b = await second.json();
  assert.match(a.owner, /^[a-f0-9]{64}$/);
  assert.notEqual(a.owner, b.owner);
  assert.equal((await get(cookieOf(first))).status, 200);
  assert.deepEqual(await (await get(cookieOf(first))).json(), a);
  assert.equal((await get(cookieOf(first))).headers.get("set-cookie"), null);
});

test("missing, unsigned, tampered, expired and ambiguous credentials fail uniformly", async () => {
  clock += 60_001;
  const first = await post();
  const cookie = cookieOf(first);
  for (const bad of [undefined, `${ANONYMOUS_COOKIE}=chosen-by-attacker`,
    cookie.slice(0, -8) + "AAAAAAAA", `${cookie}; ${cookie}`]) {
    const response = await get(bad);
    assert.equal(response.status, 404);
    assert.deepEqual(await response.json(), { detail: "Evaluation not found" });
    assert.equal(response.headers.get("set-cookie"), null);
  }
  clock += SESSION_SECONDS * 1000;
  assert.equal((await get(cookie)).status, 404);
});

test("invalid POST credentials rotate to a server-chosen session, never fixate", async () => {
  clock += 60_001;
  const invalid = `${ANONYMOUS_COOKIE}=attacker-chosen-id`;
  const response = await post(invalid, { "X-SADA-Owner": "a".repeat(64) });
  assert.equal(response.status, 201);
  assert.notEqual(cookieOf(response), invalid);
  assert.notEqual((await response.json()).owner, "a".repeat(64));
});

test("cross-origin submissions are blocked before cookies can be set", async () => {
  const blocked = await post(undefined, { Origin: "https://hostile.example" });
  assert.equal(blocked.status, 403);
  assert.equal(blocked.headers.get("set-cookie"), null);
  const missingOrigin = await fetch(base, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: "{}",
  });
  assert.equal(missingOrigin.status, 403);
  assert.equal(missingOrigin.headers.get("set-cookie"), null);
  const crossSite = await post(undefined, { "Sec-Fetch-Site": "cross-site" });
  assert.equal(crossSite.status, 403);
  assert.equal(crossSite.headers.get("set-cookie"), null);
  assert.throws(() => createAnonymousSession("short"), /SESSION_SECRET/);
});

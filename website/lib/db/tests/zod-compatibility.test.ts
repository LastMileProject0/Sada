import assert from "node:assert/strict";
import { test } from "node:test";
import { createInsertSchema } from "drizzle-zod";
import { evaluationResults } from "../src/schema/evaluations";
import { HealthCheckResponse } from "../../api-zod/src/generated/api";

test("generated health schema preserves its public data contract on Zod 4", () => {
  assert.deepEqual(HealthCheckResponse.parse({ status: "ok", privateExtra: "discard" }),
    { status: "ok" });
  for (const invalid of [null, {}, { status: 1 }, { status: ["ok"] }]) {
    assert.equal(HealthCheckResponse.safeParse(invalid).success, false);
  }
});

test("existing drizzle-zod peer supports patched Zod without a database connection", () => {
  const schema = createInsertSchema(evaluationResults);
  const row = { id: "synthetic", result: '{"note":"اختبار"}',
    createdAt: "2026-11-06 00:00:00", ownerSessionHash: null };
  assert.deepEqual(schema.parse(row), row);
  assert.equal(schema.safeParse({ ...row, ownerSessionHash: ["invalid"] }).success, false);
  assert.equal(schema.safeParse({ ...row, createdAt: undefined }).success, false);
});

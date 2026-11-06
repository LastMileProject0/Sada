import assert from "node:assert/strict";
import { test } from "node:test";
import { readFileSync } from "node:fs";
import { getTableConfig, PgDialect } from "drizzle-orm/pg-core";
import { evaluationResults } from "../src/schema/evaluations";

test("managed schema mirrors the approved private Python store without connecting", () => {
  const table = getTableConfig(evaluationResults);
  assert.equal(table.name, "evaluation_results");
  assert.deepEqual(table.columns.map(c => [c.name, c.getSQLType(), c.notNull]), [
    ["id", "text", true], ["result", "text", true],
    ["created_at", "text", true], ["owner_session_hash", "text", false],
  ]);
  assert.equal(table.columns[0].primary, true);
  assert.ok(table.columns.every(c => !c.hasDefault));
  const dialect = new PgDialect();
  const canonical = readFileSync("backend/sada_bridge/postgres_schema.sql", "utf8");
  for (const constraint of table.checks) {
    assert.ok(canonical.includes(constraint.name));
    const expression = dialect.sqlToQuery(constraint.value).sql
      .replace(/"evaluation_results"\./g, "").replace(/"/g, "");
    assert.ok(canonical.includes(expression), `Unreviewed check: ${constraint.name}`);
  }
  assert.equal(table.checks.length, 3);
  const idx = table.indexes[0].config;
  assert.equal(idx.name, "evaluation_results_owner_id");
  assert.deepEqual(idx.columns.map(c => "name" in c ? c.name : ""), ["owner_session_hash", "id"]);
  assert.equal(dialect.sqlToQuery(idx.where!).sql, '"evaluation_results"."owner_session_hash" IS NOT NULL');
});

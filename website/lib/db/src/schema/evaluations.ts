import { sql } from "drizzle-orm";
import { check, index, pgTable, text } from "drizzle-orm/pg-core";

// Mirrors backend/sada_bridge/postgres_schema.sql exactly. Definition only:
// importing this file never connects, creates a schema, or copies SQLite data.
export const evaluationResults = pgTable("evaluation_results", {
  id: text("id").primaryKey(),
  result: text("result").notNull(),
  createdAt: text("created_at").notNull(),
  ownerSessionHash: text("owner_session_hash"),
}, (table) => [
  check("evaluation_results_result_bytes", sql`octet_length(${table.result}) <= 262144`),
  check("evaluation_results_result_object", sql`jsonb_typeof(${table.result}::jsonb) = 'object'`),
  check("evaluation_results_owner_format", sql`${table.ownerSessionHash} ~ '^[0-9a-f]{64}$'`),
  index("evaluation_results_owner_id").on(table.ownerSessionHash, table.id)
    .where(sql`${table.ownerSessionHash} IS NOT NULL`),
]);

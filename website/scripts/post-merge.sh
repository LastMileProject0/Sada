#!/bin/bash
set -e
pnpm install --frozen-lockfile
# Schema preparation is code-only until the owner approves the target and diff.
# Do not implicitly mutate an inherited DATABASE_URL after an unrelated merge.
# Managed production schema changes belong to the separately approved Publish flow.

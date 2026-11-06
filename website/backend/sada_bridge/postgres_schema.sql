-- Development schema source only. Never executed by application startup/build.
CREATE TABLE IF NOT EXISTS public.evaluation_results (
  id text PRIMARY KEY,
  result text NOT NULL
    CONSTRAINT evaluation_results_result_bytes CHECK (octet_length(result) <= 262144)
    CONSTRAINT evaluation_results_result_object CHECK (jsonb_typeof(result::jsonb) = 'object'),
  created_at text NOT NULL,
  owner_session_hash text NULL
    CONSTRAINT evaluation_results_owner_format CHECK (owner_session_hash ~ '^[0-9a-f]{64}$')
);
CREATE INDEX IF NOT EXISTS evaluation_results_owner_id
  ON public.evaluation_results (owner_session_hash, id)
  WHERE owner_session_hash IS NOT NULL;

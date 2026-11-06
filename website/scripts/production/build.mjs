import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../", import.meta.url));
function run(command, args, env = {}) {
  const result = spawnSync(command, args, {
    cwd: root, stdio: "inherit", env: { ...process.env, ...env },
  });
  if (result.error || result.status !== 0) process.exit(result.status || 1);
}
// Verify the exact dependency folder that ships, not an inherited dev-only path.
run("python", ["-c",
  "import runpy; runtime=runpy.run_path('scripts/production/run.py'); "
  + "runtime['prepare_python_runtime'](); "
  + "import fastapi,uvicorn,pandas,openpyxl,pydantic,psycopg; "
  + "print('Packaged Python import preflight: PASS')",
]);
run("pnpm", ["--filter", "@workspace/api-server", "run", "build"]);
if (!process.argv.includes("--api-only")) {
  run("pnpm", ["--filter", "@workspace/sada", "run", "build"], {
    NODE_ENV: "production", BASE_PATH: "/", PORT: "22876",
  });
}

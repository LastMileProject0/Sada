# Results report browser regressions

Start the existing `artifacts/sada: web` workflow, then run:

```sh
pnpm --filter @workspace/sada run test:e2e
pnpm --filter @workspace/sada run typecheck:e2e
```

On Replit the config uses the supplied Nix-wrapped Chromium. Elsewhere first
run `pnpm --filter @workspace/sada exec playwright install --with-deps chromium`,
or set `SADA_E2E_CHROMIUM_PATH` to a working local Chromium executable.

The default URL is the shared preview proxy, `http://localhost:80/`.
Set `SADA_E2E_BASE_URL` to a running preview URL (with a trailing slash,
including any artifact base path) when running elsewhere. Do not point these
tests at production: the loading/error harness is a Vite development entry,
not a production route.

The normal `/results` page is tested in fresh browser contexts starting in
Arabic and English. Each test enters the verified demo, saves and reads an
actual HTML download, switches language without leaving demo, saves again,
and exits demo. Saved bytes are rendered in a separate browser document to
check language, direction, and visible provenance/safety warnings.

Loading/error tests mount the same Results page, real results hook, and real
providers from `fixtures/results.html`. Only that fixture injects a
`ResultsAdapter`; Playwright holds and intercepts its request to exercise
loading, HTTP failure, invalid schema, and retry. This neither connects nor
changes the default disconnected backend. The fixture is not included in
Vite's production build entry.

Downloads, screenshots, and failure traces go to the ignored
`generated-artifacts/sada-e2e/` directory at the workspace root.

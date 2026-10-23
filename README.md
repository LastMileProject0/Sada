# LastMile AI — Step 2 Project Starter

**AI-Powered Multi-Agent Emergency Communication & Resilience System**

Owner: Sirin (Project Setup & Integration). Team: Salma, Ethar, Maymona.

## Current status

This repository is the **working Python project scaffold** for Step 2. It is **not** a finished emergency-warning simulator. The bootstrap check tests only project setup and the presence of approved source files. It does not compute delivery outcomes, KPIs, or legal compliance.

All resident data, events and channel assumptions are **synthetic**. This prototype sends **no real alerts**.

## Run (Windows PowerShell)

```powershell
cd lastmile_ai_step2_starter
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m lastmile_ai --check
python -m unittest discover -s tests -v
```

If PowerShell blocks activation, you can use `.venv\Scripts\python.exe -m lastmile_ai --check` instead. On macOS/Linux, activate with `source .venv/bin/activate`.

**Success is:** `PROJECT SETUP: PASS`, followed by a clear note that agents and simulation are not implemented yet.

## Approved reference files

- `docs/reference/LastMile_AI_Step1_Master_Document.docx` — controlling requirements and approved decisions.
- `data/reference/LastMile_AI_Step1_Master_Dataset.xlsx` — Ethar's approved master input workbook. **Do not alter the reference in place.**
- `docs/integration_handoff.md` — agreed file locations and rules for integration.

The workbook is a *source of inputs only*. It does **not** contain generated warning delivery attempts or measured recovery outcomes.

## Folder map

```text
lastmile_ai/             Python package (startup + later agent modules)
  agents/                Agent implementations, added after contracts are agreed
  data/                  Dataset-loading code (Ethar)
  knowledge/             Curated sources + warning fixture (Maymona)
  reporting/             Dashboard/report calculations (later phase)
config/                  Bootstrap metadata only, NOT Salma's agent schemas
 data/reference/         Immutable source workbook
 docs/reference/         Master Step 1 document
 docs/                   Handoffs and future agent contracts
 tests/                  Smoke tests and future dataset/unit tests
```

## Independent handoffs (Step 2)

- **Salma:** `schemas.py`, `agent_contracts.md`, structured agent input/output examples.
- **Ethar:** `load_dataset.py`, `test_dataset.py`, count-validation results. Do not change the original workbook.
- **Maymona:** `sources_registry.json`, `warning_fixture.json`, `channel_actionability.md`.
- **Sirin:** repository, folders, `README.md`, `requirements.txt`, `.gitignore`, bootstrap check and later integration.

Each teammate can work independently. Use a separate branch/pull request or submit the exact files for asynchronous review. Do **not** merge automatically without comparing schema column names and data types to the approved workbook.

## Github quick start

1. Create a GitHub repository named `lastmile-ai` (prefer **Private** while preparing the team project).
2. Upload the contents of this starter folder to the repository's root (or clone and commit/push with Git).
3. Invite Salma, Ethar, and Maymona as collaborators.
4. Ask each contributor to use a branch or Pull Request; review changes before merging into `main`.
5. Never upload API keys, access tokens, or `.env` files.

Suggested initial commit message: `chore: initialize approved LastMile AI Step 2 scaffold`.

## Out of scope for this initial handoff

No CAP validator; no real network integration; no external recovery channels; no actual AI simulation or KPI calculations; no assumption that sirens alone give actionable instructions.

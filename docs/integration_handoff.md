# Step 2 — Integration Handoff (Sirin)

## Controlling inputs

Use the approved Step 1 Master Document and Master Dataset in this repository. Later explicit Sirin-approved decisions control over older archived drafts.

## Exact teammate deliverables and suggested destination

| Contributor | Deliverable | Destination after review |
|---|---|---|
| Salma | `schemas.py` | `lastmile_ai/schemas.py` |
| Salma | `agent_contracts.md`, example JSON | `docs/agent_contracts.md`; `docs/examples/` |
| Ethar | `load_dataset.py` | `lastmile_ai/data/load_dataset.py` |
| Ethar | `test_dataset.py`, test evidence | `tests/test_dataset.py`; `docs/tests/` |
| Maymona | `sources_registry.json` | `lastmile_ai/knowledge/sources_registry.json` |
| Maymona | `warning_fixture.json` | `lastmile_ai/knowledge/warning_fixture.json` |
| Maymona | `channel_actionability.md` | `docs/channel_actionability.md` |

These paths organize handoff work; preserve each teammate's module/API contracts and agree on imports during integration.

## Approved invariants — do not silently change

- Exactly 1,000 synthetic resident IDs; A=400, B=350, C=250.
- App installed=600; CH02 nominal 70% is **not** a probability nor 700 deliveries.
- EV01: 245 SMS failures in Zone B; 5 minutes from T+02 to T+07; other stages are cumulative snapshots.
- Stage inputs: T+00/T+02/T+04/T+06, and CH01–CH05 toggles only; T+07 is not selectable.
- Four agents: Delivery Simulation; Risk Analysis; Policy & Accessibility; Recovery Planning.
- `Enabled` != `Selected` != `Potential`; potential outcomes do not count toward actual reach or risk.
- Selected attempts: Delivered at t<=30s; Delayed at 30<t<=60s; Failed after no arrival within 60s; Unavailable if hard prerequisite absent.
- `No Eligible Channel` is an assignment outcome, NOT fifth delivery status.
- Technical risk uses selected-plan attempts, not all enabled channel possibilities.
- P0 priority: SMS (CH01), Voice (CH03), App (CH02), Sirens (CH04), Signage (CH05). No fallback after failed P0 attempted send.
- Sirens alone are technical alert-only and never independently count as effective coverage.
- Warning is fixed; no text rewriting; channels may convey different actionable content.
- Only enabled CH01–CH05 permitted for recovery, P1–P3 maximum, identical conditions for comparison.
- Independent Authorization and Privacy flags; no CAP validator or certified legal conclusion.
- FR-06: four main KPIs, three dashboard sections, five-section concise report.
- Age 65+ group=150 for original dashboard; derived Policy Age 60+ group=228 for policy context ONLY.
- Individual Voice usable/Signage readable B-Lite synthetic adjustments are in audited workbook; do not overwrite them with earlier dataset revisions.

## Integration review checklist

1. Cross-check column headers and data types against `Residents` and the 17 approved workbook sheets.
2. Match Salma's `schemas.py` input/output names to Ethar's loader columns; document any mapping (do not edit master data).
3. Make Maymona's reference/fixture keys align with Salma's contracts; keep required/optional CAP fields advisory only.
4. Smoke-test imports, dataset validations, JSON fixtures and actual agent code once contributed.
5. Run full later simulation tests using identical P0 and P1–P3 stage snapshots, avoid fabricated figures.

## Review ownership

- Salma reviews Ethar field contracts.
- Ethar reviews Salma example values and type assumptions.
- Maymona reviews source/fixture boundaries and the authorization/privacy scopes.
- Sirin integrates, runs tests and merges only reviewed changes.

The initial smoke check proves the scaffold works; it is NOT an acceptance test for the AI system.

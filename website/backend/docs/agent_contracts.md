# LastMile AI — Step 2: Data Models & Agent Contracts
**Owner:** Salma · **Reference:** Step 1 Master, approved 23 Oct 2026 · **Status:** Interface design / validation tests (not a full simulation implementation)

## 1. MVP constraints
Only the **selected event stage** (`T+00:00`, `T+02:00`, `T+04:00`, `T+06:00`) and **enabled channel set** (`CH01`–`CH05`, nonempty) are planner-editable. All resident attributes, scenario settings, failure assumptions and observation times are fixed. The runtime uses the original 1,000 unique residents. No real alerts are sent.

`SimulationConfiguration` is defined in `schemas.py`. The fixed scenario controls a 60-second window. An actual selected-channel arrival by 30 seconds is `Delivered`; arrival after 30 and by 60 is `Delayed`; attempted without arrival by 60 is `Failed`; a missing hard prerequisite is `Unavailable` without an actual attempt. **No Eligible Channel** is a separate *assignment* outcome, never a fifth delivery status.

## 2. Plan and channel semantics
- **Enabled:** planner switched the channel on.
- **Eligible:** enabled and hard resident/channel prerequisites hold. Weak coverage and limited internet are indicators, not automatic exclusions.
- **Selected:** assigned for an actual plan evaluation; only attempted selected deliveries count toward technical reach and risk.
- **Potential:** enabled, unselected, counterfactual channel evaluation. Never counted as a selected attempt, reach or priority outcome.
- Fixed `P0` priority: `CH01` SMS → `CH03` Voice Call → `CH02` Mobile App → `CH04` Public Sirens → `CH05` Digital Signage. No automatic backup after a P0 selected failure.
- `CH02` needs app installation; `CH04` needs a siren area flag; `CH05` needs a signage area flag. EV03 external channel is excluded.

## 3. Agent interfaces

| Agent | Input class | Output class | Main handoff |
|---|---|---|---|
| Agent 1 — Delivery Simulation | `Agent1Input` | `Agent1Output` | Simulation config, fixed resident profiles and plan assignments → separate selected delivery records, potential evaluations and no-eligible assignments |
| Agent 2 — Risk Analysis | `Agent2Input` | `Agent2Output` | Actual selected results and resident context → one resident-level `ResidentRiskFinding` with `High/Medium/Low`, evidence and separate accessibility review flag |
| Agent 3 — Policy & Accessibility | `Agent3Input` | `Agent3Output` | Warning/actionability/source fixture IDs, original profile, selected delivery and risk findings → accessibility results, independent Authorization and Privacy findings, CAP advisory |
| Agent 4 — Recovery Planning | `Agent4Input` | `Agent4Output` | P0 metrics, risk, accessibility/policy, residents and configuration → up to 3 proposed/tested candidates, selection or no-suitable result, comparison and unresolved notes |

### Agent 1 — Delivery Simulation
`ResidentProfile` is a Python-friendly transcription of the Master Dataset's **Residents** sheet: `Resident ID`, `Zone`, `Age`, `Elderly 65+`, `Hearing impairment`, `Visual impairment`, `Limited internet`, `Weak mobile coverage`, `Emergency app installed`, `In siren area`, `In signage area`, `SMS failed EV01`, `Voice usable`, `Signage readable`, `Policy Age 60+`. Ethar's loader must map columns to these exact snake_case attributes, not rename/edit the source workbook.

`DeliveryRecord` stores `resident_id`, `plan_id`, `channel_id`, `status`, `selected_in_plan`, `attempted`, `attempt_time_seconds`, `arrival_time_seconds`, `reason`, and `evidence`. The field `arrival_time_seconds` means *elapsed time after an attempt*, not a timestamp relative to scenario T+00. The schema rejects impossible timing/status combinations and duplicates. `Agent1Output.validate_against_input()` checks cross-file assignment consistency; it must be called by orchestration.

### Agent 2 — Risk Analysis
`Agent2Input` carries baseline config, Agent 1 input and results. Risk rules depend on **actual selected** arrivals only: `High` = no arrival within 60 seconds (includes no eligible channel); `Medium` = selected arrival(s), all after 30 seconds; `Low` = at least one selected timely arrival. Disability alone must never elevate technical risk. `accessibility_review_needed` is independent of risk and should be set using evidence-based rules. `Agent2Output.validate_against_input(..., require_complete=True)` checks priority consistency and completeness if requested.

### Agent 3 — Policy & Accessibility
`Agent3Input` includes IDs for three external fixtures owned by Maymona (`warning_fixture.json`, `channel_actionability.md`, `sources_registry.json`) rather than inventing their contents. `Agent3Output` has per-resident/channel `AccessibilityFinding`, independent `Authorization` and `Privacy` `PolicyFinding`s, and an optional cited `CAPAdvisory` (no CAP pass/fail boolean and no legal certification). Accessibility statuses: `Usable in Simulation`, `Accessibility Barrier`, `Needs Further Review`, `Not Assessed—No Delivery`. Policy statuses for both independent checks: `No Issue Identified`, `Review Required`, `Insufficient Information`, `Not Applicable`.

**Actionability:** Public Sirens (`CH04`) alone are alert-only and **cannot** establish effective coverage. Usability and actionability must be supported by recorded attributes and fixed warning fixture. Delivery does not prove comprehension. Unknowns stay under review, not simulated as success. `.validate_against_input()` checks that accessibility verdicts concern actually arrived selected deliveries.

### Agent 4 — Recovery Planning
`Agent4Input` carries baseline P0 results/metrics and the same fixed configuration/residents. Proposed `RecoveryCandidate` plan IDs must be `P1`, `P2`, or `P3`, maximum three, and only planner-enabled channels are allowed. A candidate with unresolved applicable authorization must not be treated as testable; any candidate metrics must be the **actual** result of rerunning Agent 1 → 2 → 3, not an estimated success claim.

`Agent4Output` represents either `Plan Selected` or `No Suitable Recovery Plan Found`; the latter retains P0 and its baseline metrics. Effective warning coverage cannot regress. Improvement is measured in **percentage points**, with denominator 1,000. Beyond these structural safeguards, the **implementation must** apply the approved ranking: feasibility/safety/authorization → no regression of previously effective warnings → more resolved accessibility gaps → fewer unresolved high-risk uncovered residents → higher effective coverage → fewer extra actual attempts → stable plan ID. Per-resident no-regression and this tie-breaking hierarchy need plan evaluation/orchestration, not simple scalar schema fields.

## 4. Data handoffs and validation boundary
1. Planner → System: `SimulationConfiguration` with exactly two editable fields.
2. System → Agent 1: fixed residents, selected P0 or candidate assignments, configuration, scenario conditions.
3. Agent 1 → Agent 2: selected delivery and separately tagged potential evaluations.
4. Agent 2 → Agent 3: resident-level technical priorities/reasons and independent accessibility-review flags.
5. Agents 1–3 → Agent 4: delivery, risk, accessibility, authorization/privacy and evidence.
6. Agent 4 → Agent 1 → Agent 2 → Agent 3: rerun each valid candidate under **identical** stage/resident/failure/timing assumptions.
7. System → Planner: four KPI cards, three dashboard sections and five report sections, using only computed evidence.

## 5. Scope & deferred integration checks
This package defines Python `dataclass` contracts, enums, validators, example JSON and unit tests; it does **not** implement data loading, simulation logic, recovery search, CAP compliance automation, messaging, or dashboard rendering. A small one-resident unit fixture does not constitute a 1,000-resident integration test. Some contract checks (e.g. full roster, feasibility of backups, no regression per previously covered resident, and evidence validity against the actual Maymona fixtures) must be performed at integration time.

**Team coordination:** Ethar validates data field names, types and 1,000-person roster; Maymona validates references/actionability and policy findings; Sirin integrates and executes end-to-end tests. Changes must follow the approved Master without altering the original dataset.

## 6. Example JSON
See `simulation_configuration_example.json` and four `examples/agent*_output_example.json` files. Their sample resident results are deliberately *illustrative*, **not** computed from the Master Dataset. The extra `example_only` key is descriptive metadata for sample files, not a dataclass attribute; strip it before instantiating an output object.

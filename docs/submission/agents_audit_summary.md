# SADA AI — Four Agents & Auditability Summary

## Purpose and scope

This document describes the four-agent workflow and the evidence available in the current SADA/LastMile AI repository. It is documentation only: no Agent implementation, simulation rule, shared schema, or source dataset is changed by this document.

The simulation uses the fixed 1,000-resident scenario and a 60-second observation window. The planner may edit only the selected event stage and enabled channel set. No live emergency alerts are sent. Counts are model outputs under documented synthetic assumptions, not observed population outcomes, legal clearance, or proof of comprehension.

## Four-agent responsibilities

| Agent | Responsibility | Main inputs | Main outputs |
|---|---|---|---|
| **Agent 1 — Delivery Simulation** | Evaluates actual selected channel assignments under deterministic timing, channel prerequisites, failures, and scenario events. | `SimulationConfiguration`; fixed `ResidentProfile` records; plan assignments (`P0` or a candidate); scenario conditions. | `Agent1Output`: selected delivery records, separately identified potential evaluations, and assignment outcomes. Each record includes status, attempt/arrival timing, reason, and evidence. |
| **Agent 2 — Risk Analysis** | Assigns a technical risk priority from actual selected delivery outcomes. Accessibility review is recorded separately from technical priority. | `Agent2Input`, including Agent 1 input and delivery output. | `Agent2Output`: one `ResidentRiskFinding` per resident, with `High`/`Medium`/`Low`, reason, evidence, and an independent `accessibility_review_needed` flag. |
| **Agent 3 — Policy & Accessibility** | Checks arrived selected warnings against the fixed Arabic warning/actionability fixture and documented usability evidence; evaluates Authorization and Privacy independently. | `Agent3Input`: configuration, selected delivery, Agent 2 risk findings, and IDs for the approved warning, actionability rules, and source registry; optional rendering evidence. | `Agent3Output`: resident/channel accessibility findings, separate Authorization and Privacy policy findings, and CAP advisory evidence where applicable. It does not issue legal certification or CAP pass/fail. |
| **Agent 4 — Recovery Planning** | Proposes up to three recovery candidates, requires actual integrated reruns, applies feasibility/safety/policy gates and the approved ranking, then selects a plan or retains P0. | `Agent4Input`: P0 baseline, residents, configuration, risk/accessibility/policy evidence and metrics; integrated evaluator callback. | `Agent4Output`: candidate proposals and evaluations, recommended plan or no-suitable-plan outcome, explanation, improvement measure, and unresolved review notes. |

### Important interpretation rules

- `Delivered` means arrival within 30 seconds; `Delayed` means arrival after 30 and within 60 seconds; `Failed` means attempted but no arrival within 60 seconds; `Unavailable` means a hard prerequisite is missing and no attempt is made.
- `No Eligible Channel` is an assignment status, not a delivery status.
- Technical reach includes both delivered and delayed arrivals. Effective warning coverage is stricter: timely selected arrival plus usable/actionable evidence. Public sirens alone do not establish effective coverage.
- Potential channel evaluations are counterfactual and do not count as selected attempts, reach, or risk outcomes.
- Missing usability/rendering evidence remains unknown or requires review; it is not automatically treated as success or as proof that a resident could not understand the warning.

## Scenario timeline: cumulative snapshots

The stage values are cumulative scenario snapshots, not separate unrelated experiments. The same fixed resident population and enabled-channel configuration are used when comparing plans at a given stage.

| Stage | Scenario state | Operational interpretation |
|---|---|---|
| **T+00:00** | Baseline; EV01 SMS outage is not active. EV02 and EV03 are not active. | P0 baseline and candidate comparisons can be evaluated without the later event conditions. |
| **T+02:00** | EV01 is active. Deterministic SMS failures affect the flagged residents in Zone B. | For residents meeting the Zone B and `sms_failed_ev01` conditions, affected SMS attempts fail. |
| **T+04:00** | EV01 remains active; EV02 accessibility conditions become active. | Accessibility barriers/review are evaluated in addition to the continuing EV01 outage. EV02 does not itself create a technical channel failure. |
| **T+06:00** | EV01 and EV02 remain active; EV03 policy-review conditions become active. | Authorization and Privacy review findings are added for the hypothetical excluded external channel/data-sharing route. The EV03 review does not change internal CH01–CH05 delivery or serve as an internal fallback. |

### Event definitions

- **EV01 — SMS outage:** At T+02, T+04 and T+06, the deterministic outage affects the relevant Zone B residents whose fixed profile has `sms_failed_ev01`. It is a scenario-specific failure layered onto the base deterministic channel model.
- **EV02 — Accessibility barriers:** Begins at T+04 and remains active at T+06. It represents accessibility conditions, not an automatic technical delivery failure. Voice usability and digital-signage readability are assessed using recorded profile/evidence; unknown rendering or playback evidence remains unknown.
- **EV03 — Authorization & Privacy review:** Begins at T+06. The documented findings concern a hypothetical outside channel/external sharing route that is excluded from the candidate plans. These are scenario-scoped review findings, not legal advice, a determination of UAE-law compliance, or authorization to deploy.

## Traceability example: Agent 1 → Agent 4

The following describes the evidence handoff for one resident record; it is a workflow illustration, not a claim about a named resident or a separately logged production event.

1. **Agent 1 — delivery evidence:** The selected assignment identifies the resident, plan ID, and channel. Agent 1 records whether an attempt occurred, its delivery status, arrival time (elapsed seconds after attempt), reason, and evidence. A potential/unselected channel result is kept separate.
2. **Agent 2 — technical risk:** Agent 2 consumes only selected delivery records. A timely selected arrival supports `Low` technical risk; an arrival only after 30 seconds supports `Medium`; no arrival within 60 seconds (or no eligible channel) supports `High`. A known selected voice/signage barrier can set the separate accessibility-review flag; disability alone does not raise technical risk.
3. **Agent 3 — accessibility and policy evidence:** Agent 3 evaluates an arrived selected warning against the fixed Arabic warning/actionability fixture and available individual/rendering evidence. It returns a usability/actionability finding and independent Authorization and Privacy findings. Delivery alone does not prove complete SMS multipart receipt, completed audio playback, usability, or comprehension.
4. **Agent 4 — candidate verification and selection:** Agent 4 receives the P0 baseline and the Agent 2/3 evidence, proposes P1–P3, and relies on actual reruns of Agents 1–3 under the same stage, residents, enabled channels, and scenario assumptions. Candidate metrics are computed from those reruns; they are not forecasts. The resulting plan decision and reasons are recorded in the Step 4 comparison report.

The integrated runtime implements this loop in `lastmile_ai/recovery_runtime.py`. It recomputes effective resident IDs from timely selected delivery intersected with Agent 3's usable/actionable findings and checks that this agrees with the existing effective-coverage metric.

## Step 4 plan comparison and why P3 was selected

The reproducible comparison command was run for `T+00:00` with all five channels enabled. The actual output is preserved in `step4_T00_comparison.md` alongside this summary.

| Plan | Selected | Technical reach | Effective coverage | Δ effective vs P0 | Unresolved critical |
|---|---:|---:|---:|---:|---:|
| P0 | No | 961 | 0 | +0 | 39 |
| P1 | No | 939 | 0 | +0 | 61 |
| P2 | No | 934 | 0 | +0 | 66 |
| P3 | **Yes** | 946 | 366 | +366 | 54 |

**P3 was selected** because the integrated run reports it as authorized for the scenario, safe/feasible, and verified, and it is the only candidate in this comparison with confirmed effective coverage improvement over P0. It produces 366 effective residents (36.6 percentage points out of 1,000), compared with 0 for P0, P1, and P2.

This selection has a visible trade-off: P3's technical reach (946) is lower than P0's (961), and its unresolved critical count (54) is higher than P0's (39). Therefore, the result must be described as an improvement in **effective coverage**, not an improvement in every KPI. The comparison report also records why P1 and P2 were not selected: neither improved effective coverage over P0. “No Issue Identified” in this run is limited to the documented synthetic scenario and is not real-world legal authorization.

## Audit trail: what is and is not evidenced

### Evidence available in the repository

- Typed input/output contracts and validation methods in `lastmile_ai/schemas.py`.
- Agent-specific outputs containing reasons and evidence references.
- Fixed warning and source fixtures under `lastmile_ai/knowledge/`.
- Reproducible deterministic delivery rules in `lastmile_ai/agents/delivery.py` and scenario switches in `lastmile_ai/agents/scenario_conditions.py`.
- Integrated baseline and candidate reruns in `lastmile_ai/recovery_runtime.py`.
- A generated Markdown comparison report containing plan metrics, selection, candidate reasons, and interpretation cautions (`analysis/step4_compare_plans.py`).

### Limitations — do not overclaim

- The reviewed implementation provides structured in-memory evidence and a generated comparison report. This review did **not** establish a durable, tamper-evident, append-only audit-log service, external timestamping, or a production event-retention mechanism.
- The report is reproducible output for a specified stage/configuration; by itself it is not a full record of every underlying resident-level event.
- Synthetic deterministic assumptions are not measured network performance or field validation.
- Unknown SMS multipart completeness, voice playback completion, and individual app/text usability cannot be silently converted into confirmed success.
- The EV03 Authorization/Privacy result is a scenario review only, not a legal opinion, compliance certification, or deployment approval.
- The sample JSON files in `docs/examples/` are illustrative; their sample resident results are not computed outputs from the Master Dataset.
- The existing unit tests and one stage comparison do not, by themselves, establish production readiness or validate every stage in a live operational environment.

## Evidence and implementation references

- `docs/agent_contracts.md` — agent contracts, handoffs, semantics, and validation boundary.
- `docs/agent1_timing_decision.md` — deterministic hash, synthetic timing/failure assumptions, event treatment, and delivery status thresholds.
- `docs/agent3_runtime_handoff.md` — Agent 3 evidence requirements, accessibility interpretation, policy limitations, and MVP limits.
- `lastmile_ai/agents/delivery.py` — Agent 1 delivery model.
- `lastmile_ai/agents/risk.py` — Agent 2 risk analysis.
- `lastmile_ai/agents/policy_accessibility.py` and `lastmile_ai/agents/evaluation.py` — Agent 3 policy/accessibility and content-actionability checks.
- `lastmile_ai/agents/recovery.py` — Agent 4 candidate proposal and selection rules.
- `lastmile_ai/recovery_runtime.py` — integrated candidate reruns and effective-coverage evidence.
- `analysis/step4_compare_plans.py` — reproducible plan comparison report.
- `tests/test_step4_plan_comparison.py` — Step 4 comparison/audit tests.
- `step4_T00_comparison.md` — generated T+00 comparison evidence included with this submission.

# LastMile AI — Step 3 | Salma's Agent 2 + Agent 4

## Deliverables
- `risk.py`: Agent 2 actual-selected-delivery risk classification and independent accessibility-review flags.
- `test_agent2_runtime.py`: 8 unit tests.
- `recovery.py`: Agent 4 limited three-plan proposal generator, verification gate, approved ranking, and safe fallback to P0.
- `test_agent4_runtime.py`: 10 unit tests.
- `schemas.py`: **Unchanged reference copy** of Salma's Step 2 schema, included only so these modules run; do not overwrite the integrated canonical schema without checking.

## Agent 2 evaluation rules
- **High**: no actual selected arrival within 60 seconds, including No Eligible Channel.
- **Medium**: at least one selected delayed arrival (31–60 seconds), with no on-time selected arrival.
- **Low**: at least one selected arrival within 30 seconds.
- A hypothetical/potential channel outcome never changes technical risk.
- `accessibility_review_needed` is independent: known inability to use a **selected** Voice Call (`voice_usable=False`) or read **selected** Digital Signage (`signage_readable=False`) triggers review; disability presence alone does not.
- Each finding includes simulation evidence and any relevant resident accessibility-profile evidence.

## Agent 4 proposal and selection
- Proposes P1, P2, P3 using different *priority orders* over channels that the planner enabled. Uses the hard prerequisites for App, Sirens, and Signage. Weak coverage and limited internet do **not** automatically disqualify channels.
- Avoids selected Voice/Signage with explicit known usability barriers; tries sirens last because sirens alone do **not** create Effective Warning Coverage. Actual access/actionability still must be verified by Agent 3.
- Residents already effectively covered by P0 retain their previously assigned channel in the proposal. The pipeline must **still verify** no regression by individual resident.
- The function `run_agent4(...)` accepts an `evaluate(candidate)` callback supplied by Sirin's pipeline, which must rerun Agents 1 → 2 → 3 at the same configuration, residents and timing and recompute actual metrics. The callback returns `VerifiedEvaluation` containing `PlanMetrics`, the set of effectively covered resident IDs, candidate authorization result, explicit safety decision, and explanation.
- Without the callback, proposals remain untested and P0 is kept. Unknown authorization is **not** implicitly approved.
- Candidates are gated on authorization **No Issue Identified**, safety approval, and no previously effective individual losing coverage. Candidate metrics are displayed only for candidates passing the safety and authorization gates.
- A winning candidate must improve overall effective coverage over P0. Tie-break: greater resolved accessibility gaps; then fewer unresolved critical cases; then higher effective coverage; then fewer added selected attempts; then stable plan ID.
- A missing/invalid evaluator or inconsistent effective-coverage resident roster is rejected (or handled conservatively where no evaluator was supplied). No generated statistics are presented as real simulation outcomes.

## Integration dependencies for Sirin (must be addressed before end-to-end demo)
1. The Step 2 `Agent4Input` does **not** contain P0 `PlanAssignment` records or a roster of effectively covered residents. The orchestrator must supply both as `baseline_assignments` and `baseline_effective_ids` (for example from computed Agent 1/3 findings), after confirming exact consistency.
2. The current schema allows **one** `PlanAssignment.selected_channel` per resident. Therefore this Agent 4 implementation compares alternative **single-channel assignments**, not true multi-channel sequential fallback plans. Any multi-attempt expansion requires a separately approved schema change and coordinated Agent 1 implementation.
3. Sirin must implement/adapt the evaluator callback to run Agent 1 / Agent 2 / Agent 3 with the same synthetic resident roster and fixed event-stage conditions, check eligibility, authorization, safety and privacy, and derive unique effective resident IDs and KPIs. There is NO completed end-to-end 1,000-resident simulation in this package.
4. Verify candidate-specific authorization/Privacy and accessibility fixtures with Maymona. `authorization_status=No Issue Identified` in synthetic tests is a **test stub**, never a claim of legal approval.
5. In the approved schema, `PlanMetrics.resolved_accessibility_gaps` and `unresolved_critical_count` are inputs computed by the pipeline; `recovery.py` never estimates them.
6. Pipeline should validate actual attempts, hard prerequisites, real agent outputs, duplicate plans, and the evidence trail; synthetic unit-test mocks do not prove integration.

## How to run
Place files together and run:

```bash
python -m unittest -v test_agent2_runtime.py test_agent4_runtime.py
```

Current result: **18 unit tests passed** (8 + 10). No live warning, external data transmission, or legal certification is performed.

## Main functions for explanation/presentation
- `analyze_risk(input: Agent2Input)`: groups **selected** delivery records by resident; assigns High/Medium/Low; flags explicit channel usability barriers; emits `Agent2Output` and validates it.
- `propose_candidates(value, baseline_assignments, baseline_effective_ids)`: makes P1–P3 with legal enabled channels and fixed profile prerequisites, preserving effective baseline assignments.
- `run_agent4(value, baseline_assignments=..., baseline_effective_ids=..., evaluate=...)`: coordinates proposal verification, rejects unauthorized/unsafe/regressive plans, ranks verified improvements, returns `Agent4Output` or retains P0.
- `VerifiedEvaluation`: typed record of *actual* rerun results; an interface, not a simulation engine.

## Decisions not made by Salma
The team leader should explicitly approve whether Step 3 recovery is intentionally limited to a single selected channel per resident (compatible with the current Step 2 schema), or whether true multiple-attempt recovery warrants revising the shared schema and Agents 1/2/3 contracts.

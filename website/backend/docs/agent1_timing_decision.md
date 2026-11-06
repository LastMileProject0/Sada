# LastMile AI — Agent 1
## Deterministic Timing & Failure Rules — Version 1

### Decision Status
Approved by the team leader during Step 3.

These numerical timing and failure parameters are new Step 3
synthetic modeling assumptions, not original Step 1 parameters.

### Deterministic Hash
- Algorithm: SHA-256
- Encoding: UTF-8
- Model version: lastmile-timing-v1
- Key: model_version|resident_id|channel_id|calculation_type
- Calculation types: failure, delay
- First 8 SHA-256 bytes interpreted as unsigned big-endian integer
- Normalization: integer / 2**64, giving a value in [0, 1)
- plan_id and selected_stage are excluded from the base hash.

### Approved Channel Parameters

| Channel | Base Delay | Base Failure |
|---|---|---|
| CH01 SMS | 8–25 seconds | 5% |
| CH02 Mobile App | 5–20 seconds | 8% |
| CH03 Voice Call | 10–30 seconds | 7% |
| CH04 Public Sirens | 3–12 seconds | 3% |
| CH05 Digital Signage | 5–15 seconds | 5% |

All parameters are synthetic assumptions, not measured network performance.

### Delay Calculation
base_delay = min_delay + int(hash_delay * (max_delay - min_delay + 1))

Both delay bounds are inclusive.

### Network Conditions
- Weak Mobile Coverage: +15 seconds for SMS and Voice Call.
- Limited Internet: +20 seconds for Mobile App.
- These conditions do not automatically cause Unavailable.

### Cumulative Events
- EV01: At T+02, T+04 and T+06, affected Zone B SMS attempts
  deterministically fail.
- EV02: Accessibility barriers; no automatic technical failure.
- EV03: Authorization/privacy review; no technical delivery change.

### Evaluation Order
1. Check hard prerequisites.
2. Apply deterministic scenario outage (EV01).
3. Apply SHA-256 base failure.
4. Calculate integer base delay.
5. Add approved network penalty.
6. Classify delivery outcome.

### Delivery Status
- Delivered: arrival <= 30 seconds.
- Delayed: arrival > 30 and <= 60 seconds.
- Failed: attempted, with no arrival within 60 seconds.
- Unavailable: missing hard prerequisite; no attempt.

No Eligible Channel is an assignment status, not a delivery status.

### Plan Fairness
- Same timing rules apply to P0, P1, P2 and P3.
- plan_id does not affect technical delivery.
- selected_stage affects applicable scenario events, not the base hash.
- Potential evaluations do not count as actual attempts.
- No automatic fallback in P0.

### Validated P0 Simulation Results
All five channels enabled; 1,000 synthetic residents.

| Stage | Delivered | Delayed | Failed |
|---|---:|---:|---:|
| T+00 | 904 | 57 | 39 |
| T+02 | 677 | 45 | 278 |
| T+04 | 677 | 45 | 278 |
| T+06 | 677 | 45 | 278 |

At T+02, 245 SMS failures are caused by EV01.

### Testing
- 15 unit tests passed (including channel-prerequisite and timeout-path tests).
- Full 1,000-resident simulation completed.
- All four event stages evaluated.
- Regression results remained unchanged after Evidence enhancement.

### Scope
Agent 1 models technical delivery only.
Accessibility judgments belong to Agent 3.
Recovery selection belongs to Agent 4.
The Master Dataset and shared schemas were not modified.

### Integration Handoff Notes
- `delivery.py` and `scenario_conditions.py` currently import `schemas` as a top-level module; adjust import paths when integrating into the `lastmile_ai` package, then rerun tests.
- The 1,000-resident run used validated resident profiles and P0 assignments assembled in Jupyter; the production orchestration must supply valid `Agent1Input` assignments.
- A planner-enabled but resident-ineligible selected channel currently yields a selected `Unavailable` record with no attempt. The assignment-producing layer should validate plan eligibility; review this handoff behavior during integration rather than changing the shared schema without approval.
- Full package-level GitHub integration has not yet been tested.

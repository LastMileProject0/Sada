# LastMile AI — Step 4 Scenario Validation Report

**Workstream:** Scenario QA & Reproducibility

**Responsible Team Member:** Ethar

**Project:** LastMile AI — الإنذار اللي ما وصل

**Date:** October 30, 2026

**Validation Scope:** Step 4 — Approved Synthetic Scenario

## 1. Objective

This report documents the validation of the approved LastMile AI synthetic emergency-warning scenario.

The objective is to verify reproducibility, delivery timing boundaries, channel eligibility, cumulative event behavior, and scenario consistency without modifying the approved Master Dataset or the existing Agent 1 implementation.

Validation was performed against the actual integrated baseline implementation using 1,000 synthetic resident profiles.

## 2. Test Environment

| Component        | Description                                                 |

| ---------------- | ----------------------------------------------------------- |

| Operating system | Windows                                                     |

| Python version   | 3.14.10                                                     |

| Test framework   | Python unittest                                             |

| Dataset          | LastMile AI Step 1 Master Dataset                           |

| Residents        | 1,000 synthetic profiles                                    |

| Channels         | SMS, Mobile App, Voice Call, Public Sirens, Digital Signage |

| Scenario stages  | T+00, T+02, T+04, T+06                                      |

| Evaluated plan   | P0 — Standard Baseline                                      |

### Test Command

Run the following command from the project root:

```powershell

python -m unittest discover -s tests -p "test_step4_scenario_validation.py" -v

```

### Observed Test Result

```text

Ran 10 tests in 2.760s

OK

```

**Overall result: PASS — 10/10 tests.**

The existing project test suite was executed successfully before adding the Step 4 validation tests:

```text

Ran 127 tests in 3.255s

OK

```

The complete project test suite was rerun after adding the Step 4 tests:

```text
Ran 137 tests in 5.020s

OK
```

## 3. Validation Checklist

| ID    | Validation Area                                             | Result |

| ----- | ----------------------------------------------------------- | ------ |

| QA-01 | Deterministic reproducibility under identical configuration | PASS   |

| QA-02 | Reject configurations with zero enabled channels            | PASS   |

| QA-03 | Delivered, Delayed, and Failed timing boundaries            | PASS   |

| QA-04 | No Eligible Channel and Unavailable behavior                | PASS   |

| QA-05 | Four-stage simulation with all five channels enabled        | PASS   |

| QA-06 | Individual-channel execution at T+02                        | PASS   |

| QA-07 | Cumulative activation of EV01, EV02, and EV03               | PASS   |

| QA-08 | EV01 SMS outage in Zone B                                   | PASS   |

| QA-09 | EV02 accessibility barrier data at T+04                     | PASS   |

| QA-10 | P0 delivery-result consistency across four stages           | PASS   |

## 4. Four-Stage Scenario Validation

All five approved channels were enabled when evaluating the four scenario stages.

### Observed P0 Delivery Results

| Stage | Delivered | Delayed | Failed | Unavailable | No Eligible Channel |

| ----- | --------: | ------: | -----: | ----------: | ------------------: |

| T+00  |       904 |      57 |     39 |           0 |                   0 |

| T+02  |       677 |      45 |    278 |           0 |                   0 |

| T+04  |       677 |      45 |    278 |           0 |                   0 |

| T+06  |       677 |      45 |    278 |           0 |                   0 |

All four stage evaluations accounted for 1,000 residents.

### Interpretation

At T+00, 961 residents had technically successful warning arrivals, including Delivered and Delayed records.

At T+02, successful technical arrivals decreased to 722, and total failures increased to 278.

The observed technical-delivery counts remained unchanged at T+04 and T+06.

This equality does not imply that EV02 and EV03 are inactive. These events affect accessibility conditions and policy-review context, respectively, rather than automatically introducing additional technical-delivery failures.

The figures represent simulated technical-delivery outcomes, not verified real-world reach, comprehension, or legal compliance.

## 5. EV01 — SMS Outage in Zone B

The approved scenario specifies an SMS outage affecting selected residents in Zone B beginning at T+02.

### Observed Results

| Check                        | Result |

| ---------------------------- | ------ |

| EV01-attributed SMS failures | 245    |

| Affected zone                | Zone B |

| Technical delivery status    | Failed |

| Attempted                    | True   |

| Arrival time                 | None   |

| Overall validation           | PASS   |

All 245 EV01-attributed records were classified as Failed rather than Unavailable.

This distinction is important: the SMS channel was eligible and attempted, but delivery failed because of the modeled outage.

The total increase in Failed records between T+00 and T+02 should not be interpreted as 245 additional independent failures. Some affected attempts may already have failed under the deterministic baseline failure rules.

## 6. EV02 — Accessibility Barriers at T+04

The approved scenario includes accessibility barriers involving Voice Call and Digital Signage.

### Verified Dataset Conditions

| Barrier                                           | Zone   | Observed Profiles |

| ------------------------------------------------- | ------ | ----------------: |

| Hearing impairment with Voice Call unusable       | Zone B |                30 |

| Visual impairment with Digital Signage unreadable | Zone B |                20 |

Both counts matched the approved scenario assumptions.

These are scenario-level accessibility attributes. They must not automatically be interpreted as technical delivery failures or as evidence that a resident could not understand the warning.

Accessibility assessment and supporting explanations are handled separately by Agent 3.

The two groups should not be assumed to contain 50 distinct residents without checking potential overlap.

## 7. Cumulative Event Activation

The cumulative event logic was evaluated at all four selectable stages.

| Stage | EV01 SMS Outage | EV02 Accessibility Conditions | EV03 Policy Review |

| ----- | --------------- | ----------------------------- | ------------------ |

| T+00  | Inactive        | Inactive                      | Inactive           |

| T+02  | Active          | Inactive                      | Inactive           |

| T+04  | Active          | Active                        | Inactive           |

| T+06  | Active          | Active                        | Active             |

**Validation result: PASS.**

At T+06, all three events are active under the approved cumulative-stage semantics.

EV03 indicates policy-review conditions; this validation does not assert that any action is legally compliant or non-compliant.

## 8. Channel Eligibility and Delivery Rules

The validation confirmed the following approved behavior:

* Delivered: arrival time less than or equal to 30 seconds.

* Delayed: arrival time greater than 30 seconds and less than or equal to 60 seconds.

* Failed: attempted delivery without arrival within the observation window.

* Unavailable: missing hard prerequisite; no actual delivery attempt.

* No Eligible Channel: assignment-level status, not a delivery status.

* Potential channel evaluations do not count as actual attempts.

* Configurations containing zero enabled channels are rejected.

Each approved channel was also executed independently at T+02.

The tests confirmed that selected records used only the enabled channel, and that each resident received either a channel assignment or a No Eligible Channel assignment.

## 9. Reproducibility

The integrated baseline was executed twice using identical configuration settings at T+02 with all five channels enabled.

The returned baseline results were compared directly.

**Result: PASS — identical results for both runs.**

This confirms deterministic reproducibility for the tested configuration and project environment.

## 10. Scope and Limitations

This validation covers the approved synthetic scenario and its implemented baseline simulation.

It does not establish real-world telecommunications performance, emergency-warning effectiveness, accessibility certification, or legal compliance.

The validation did not modify:

* `delivery.py`

* `scenario_conditions.py`

* `schemas.py`

* The approved Master Dataset

* Recovery planning or policy-assessment components

No discrepancies were observed in the ten completed validation tests. Additional integration testing remains the responsibility of the final integration process.

## 11. Deliverables

**Required test file:**

`tests/test_step4_scenario_validation.py`

**Required validation report:**

`docs/step4/ethar_scenario_validation.md`

**Optional matrix generator:** Not implemented; the scenario matrix was produced directly from the integrated baseline and verified through the test suite.

## 12. Final Validation Status

**Step 4 — Scenario QA & Reproducibility: PASS**

All ten dedicated validation tests passed in the local environment.

The observed scenario behavior and recorded results are consistent with the approved synthetic simulation configuration.

The validation evidence is ready for team-leader review and integration.


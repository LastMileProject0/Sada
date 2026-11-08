# SADA — Global Best Practices & Policy Gap Mapping

**Owner:** Eithar — Policy & Standards Gaps  
**Submission path:** `docs/submission/policy_gap_mapping.md`  
**Basis:** Review of the supplied SADA project archive and the official external references listed below.  
**Scope:** Four priority policy gaps and four cross-cutting review topics.

> **Important:** This mapping is a gap assessment, not a compliance certificate. The existence of a policy reference, code component, simulation, or test does not establish full compliance with the corresponding external standard. Statuses apply only to the bounded SADA behavior described.

## 1. Executive mapping

| Gap                               | How identified                                                                                                                                                                   | Evidence in SADA project                                                                                                                                                                                                                                                                             | Global / official reference                                                                                        | Assessment                                                                                                                                                                                                                                                                      |
|:----------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Emergency Communication**       | Compared SADA’s emergency-warning simulation with the UAE telecom emergency-management and continuity objectives: preparedness, coordination, continuity, response and recovery. | `scenario_conditions.py` models an SMS outage in fictional Zone B across T+00/T+02/T+04/T+06. `delivery.py` models deterministic channel delivery/failure. `channel_actionability.md` documents five simulated warning channels, fixed Arabic warning content and limits (e.g. siren is alert-only). | TDRA, *National Telecom Emergency Management Plan* and *Business Resilience and Continuity in the Telecom Sector*. | **Partially Verified:** bounded simulation and recovery comparison are evidenced. **Not evidenced:** live telecom/operator integration, real alert dispatch, national coordination or operational continuity.                                                                   |
| **Accessibility**                 | Compared the warning-channel accessibility logic and website review scope with WCAG 2.2. Kept simulation accessibility separate from web accessibility.                          | `policy_accessibility.py`, `accessibility_stage.py`, `stage_accessibility_adapter.py`; tests `test_accessibility_stage_ethar.py` and `test_stage_accessibility_integration.py`. EV02 models selected voice/signage barriers; unknown usability is handled conservatively and may require review.     | W3C, *Web Content Accessibility Guidelines (WCAG) 2.2*.                                                            | **Partially Verified:** selected accessibility behavior in the simulation has code/test evidence. **Not Verified:** website-wide WCAG 2.2 conformance, full keyboard/screen-reader testing, contrast and reflow audit.                                                          |
| **Transparency & Accountability** | Compared the four-Agent workflow, typed handoffs, evidence references and reports with OECD expectations for transparency, explainability, traceability and accountability.      | `agent_contracts.md`, `schemas.py`, `pipeline.py`, `recovery_runtime.py`; structured policy findings and `Review Required` outcomes; project claim/source documentation. These support bounded workflow traceability, but not proof of a complete audit trail for every output.                      | OECD, *AI Principles* (2019; updated 2024), especially transparency/explainability and accountability.             | **Partially Verified:** agent contracts and evidence-oriented outputs exist. **Still to verify:** 2–3 end-to-end scenario traces, source-to-claim support, user-facing explanations and human review/override records.                                                          |
| **AI Risk & Cybersecurity**       | Compared SADA’s security-phase records and tests with NIST AI RMF 1.0’s Govern, Map, Measure and Manage functions.                                                               | `security-phase-2a.md`, `security-phase-2b.md`, `security-phase-3.md`, `dependency-security-review.md` document bounded protections and tests: request limits, session ownership, CSRF/origin checks, storage/backup safeguards, deployment boundaries and outstanding blockers.                     | NIST, *AI Risk Management Framework (AI RMF 1.0)*.                                                                 | **Partially Verified:** selected application-security controls and test results are documented. **Not fully evidenced:** complete AI-risk governance, AI-specific evaluation, residual-risk ownership, production ingress/storage readiness and closure of dependency findings. |

## 2. Gap details and required follow-up

### GAP-01 — Emergency Communication

**How the gap was found:** The external benchmark concerns sector-level telecommunications emergency preparedness, continuity, coordination, response and recovery. Repository inspection found a simulated warning-disruption workflow, not a live telecom emergency service.

**Evidence and interpretation:**

- `scenario_conditions.py` defines the fictional EV01 SMS outage scenario and stage timing.
- `delivery.py` models delivery timing and channel failures deterministically.
- `channel_actionability.md` describes the simulated channels and their limitations, including that sirens alone do not constitute effective warning coverage.
- The scenario is an exercise/simulation. It does not prove actual SMS, voice, siren, signage or Cell Broadcast dispatch.

**Reference:** TDRA, [Business Resilience and Continuity in the Telecom Sector](https://tdra.gov.ae/en/initiatives/business-resilience-and-continuity-in-the-telecom) and [National Telecom Emergency Management Plan](https://tdra.gov.ae/-/media/TDRA-Media/Resources/English/National-Telecom-Emergency-Management-Plan.ashx).

**Required action:** Preserve the fictional/exercise label; provide one reproducible EV01 trace; map continuity, roles, escalation, response and recovery requirements to actual prototype evidence; identify operator/authority integrations as future work unless they are demonstrably present.

### GAP-02 — Accessibility

**How the gap was found:** Repository inspection found simulation-level accessibility logic and tests. The supplied artifacts do not establish a complete WCAG audit of the public-facing website. These are different scopes and must not be conflated.

**Evidence and interpretation:**

- `policy_accessibility.py` evaluates selected delivered channels using person-level voice/signage usability and evidence.
- `scenario_conditions.py` models EV02 accessibility conditions.
- `accessibility_stage.py` and `stage_accessibility_adapter.py` implement stage-aware handling.
- `test_accessibility_stage_ethar.py` and `test_stage_accessibility_integration.py` test selected behavior, including conservative handling of unknown accessibility status.
- These tests do not establish website conformance, screen-reader compatibility, or complete real-user accessibility.

**Reference:** W3C, [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/).

**Required action:** Run and retain a WCAG 2.2 audit for Planning → Simulation → Results → Reports, Arabic and English, desktop and mobile. Include keyboard-only, focus, contrast, screen-reader, zoom/reflow, labels/errors and language metadata. Report criterion, page, reproduction steps, result and screenshot. Do not claim WCAG conformance based only on Agent 3 tests.

### GAP-03 — Transparency & Accountability

**How the gap was found:** The four-Agent architecture and report/evidence artifacts were compared with OECD principles requiring appropriate transparency, explainability and accountability across the AI lifecycle.

**Evidence and interpretation:**

- `agent_contracts.md` and `schemas.py` define structured agent contracts and typed data.
- `pipeline.py` and `recovery_runtime.py` implement orchestration and recovery execution.
- Policy findings include evidence references and review states; the EV03 external-route case is documented as requiring review rather than being silently approved.
- `maymona_claims_sources.md` warns that a valid citation ID does not by itself prove passage-level retrieval or semantic support.
- This supports traceability building blocks, not a claim that every recommendation has a complete, immutable audit trail.

**Reference:** OECD, [AI Principles](https://www.oecd.org/en/topics/ai-principles.html), updated in 2024.

**Required action:** Use 2–3 existing, unchanged SADA scenarios to trace input → stage → Agent → output → evidence reference → review state → report. Mark fields Present/Missing/Not Applicable. Include a `Review Required` example. Explain system capabilities and limitations to users; do not invent missing timestamps, source passages or approvals.

### GAP-04 — AI Risk & Cybersecurity

**How the gap was found:** The repository’s security-phase documentation and tests were assessed against NIST AI RMF 1.0. The framework’s four functions provide an organizing structure, but application-security tests alone do not demonstrate complete AI risk management.

**Evidence and interpretation:**

- Phase 2A documents request/admission limits, body/type/size protections, origin controls and bounded resource behavior.
- Phase 2B documents anonymous signed sessions, owner-bound reads, CSRF/origin checks and backup/migration safeguards.
- Phase 3 documents deployment boundaries and production blockers.
- The dependency review records findings that require attention.
- These are bounded controls and project-recorded test results, not an independent security certification.

**Reference:** NIST, [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) and [AI RMF 1.0 publication](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10).

**Required action:** Maintain a risk register organized by Govern/Map/Measure/Manage. For each risk record scenario, affected asset/user, current control and evidence, residual risk, owner, mitigation and monitoring. Recheck dependencies, ingress, storage and deployment controls on the exact release candidate before claiming production readiness.

## 3. Cross-cutting topics within the review scope

These topics are included for review and disclosure. Their inclusion does **not** mean SADA implements the corresponding policies or controls.

| Topic                              | Review question                                                                                                            | Evidence needed / current limitation                                                                                                                                                                                 |
|:-----------------------------------|:---------------------------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Privacy**                        | What data is collected, for what purpose, where is it stored, who can access it, and how long is it retained?              | Agent findings include separate Privacy/Authorization considerations and EV03 review handling. A complete deployed data inventory, retention policy and privacy assessment are not established by those flags alone. |
| **Institutional Responsibilities** | Who owns decisions, approval, escalation, incident response and coordination with authorities/operators?                   | A simulated agent workflow does not establish formal institutional delegation, operator RACI or authority adoption. These require explicit roles and approved procedures.                                            |
| **Energy / Environmental impact**  | What compute, hosting and AI usage impacts are measured or estimated?                                                      | No complete energy/compute measurement or sustainability assessment was evidenced in the reviewed project artifacts. Treat as future assessment.                                                                     |
| **Intellectual Property (IP)**     | Are code, datasets, third-party packages, model/provider terms and generated assets appropriately licensed and attributed? | A complete license and third-party asset inventory is still required. Do not claim full IP clearance without checking the repository LICENSE, notices, data/model terms and dependencies.                            |

## 4. Evidence still required before final submission

| Follow-up                                                         | Why it matters                                                                          | Owner / related task          |
|:------------------------------------------------------------------|:----------------------------------------------------------------------------------------|:------------------------------|
| Reproducible EV01 scenario trace                                  | Makes the emergency-communication evidence auditable and clearly bounded to simulation. | SADA scenario/report owner    |
| WCAG 2.2 test record for all key pages and languages              | Separates simulation accessibility logic from actual website accessibility.             | Sirin — Website QA            |
| 2–3 end-to-end Agent traces                                       | Demonstrates the real extent and limits of traceability.                                | Salma — Agents & Auditability |
| Updated risk register and release-candidate security checks       | Confirms which security findings are fixed and which remain open.                       | Sirin / technical owner       |
| Privacy, institutional responsibility, energy and IP review notes | Prevents unsubstantiated claims in the submission.                                      | Project team                  |

## 5. Overall conclusion

The supplied project artifacts support a defensible account of SADA as a synthetic emergency-warning and recovery simulation with selected accessibility-related logic, a four-Agent workflow, evidence-oriented policy findings, and documented/tested application-security controls.

The reviewed evidence does not establish that SADA is a live emergency communications platform, conforms to the TDRA telecom emergency plan, is WCAG 2.2 conformant, has a complete immutable audit trail, or fully implements NIST AI RMF. The submission should describe the bounded capabilities demonstrated by the prototype, identify the remaining verification work, and distinguish simulated outcomes from real-world operational performance.

## 6. Official references

1.  TDRA — [Business Resilience and Continuity in the Telecom Sector](https://tdra.gov.ae/en/initiatives/business-resilience-and-continuity-in-the-telecom).
2.  TDRA — [National Telecom Emergency Management Plan](https://tdra.gov.ae/-/media/TDRA-Media/Resources/English/National-Telecom-Emergency-Management-Plan.ashx).
3.  W3C — [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/).
4.  OECD — [OECD AI Principles](https://www.oecd.org/en/topics/ai-principles.html).
5.  NIST — [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework).
6.  NIST — [AI RMF 1.0, NIST AI 100-1](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10).

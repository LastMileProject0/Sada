# LastMile AI — Technical Report (Reviewed Draft)

**AI-Powered Multi-Agent Emergency Communication & Resilience System**  
**Event:** ITU AI for Good Lab Hackathon — United Arab Emirates  
**Team:** LastMile AI  
**Repository:** https://github.com/LastMileProject0/LastMile *(repository access for judges must be confirmed)*  
**Knowledge resources:** `lastmile_ai/knowledge/sources_registry.json`; evidence in `docs/step4/`  
**Status:** Reviewed draft — transfer to the official ITU submission template and verify the five-page limit.

## 1. Short Introduction to the Agentic AI Solution

LastMile AI is an **offline, pre-event emergency-communication planning prototype**. It helps planners test whether a fixed warning is estimated to reach synthetic residents, whether the selected channel can convey actionable content, and whether the warning format is usable under simulated accessibility and connectivity conditions. The solution compares a fixed-priority baseline (**P0**) with up to three recovery plans (**P1–P3**), then generates a reproducible HTML dashboard and Markdown simulation report. It **does not transmit real warnings or make operational response decisions**.

## 2. Use Case and Requirements

The exercise models a fictional flash-flood scenario, `AL_WADI_FLASH_FLOOD`, involving **1,000 synthetic residents** across **Zone A (400), Zone B (350), and Zone C (250)**. Profiles include hearing or visual accessibility needs, limited internet, weak mobile coverage and age-related factors. The same approved **Arabic warning** is used in all runs; the MVP selects and tests delivery channels rather than rewriting its text.

A planner selects one cumulative stage (**T+00, T+02, T+04, T+06**) and enables at least one of five channels: **CH01 SMS, CH02 Mobile App, CH03 Automated Voice Call, CH04 Public Sirens, CH05 Digital Signage**. The remaining scenario conditions are fixed. Delivery outcomes are `Delivered` (arrival ≤30 seconds), `Delayed` (>30 and ≤60 seconds), `Failed`, or `Unavailable` (hard prerequisites absent). The evaluation separates **technical reach, accessibility, actionable content, and scenario-based policy review**. Sirens are alert-only and cannot alone establish Effective Warning Coverage.

## 3. Solution Architecture and Mapping to ITU-T Y.3172

The system coordinates four agents:

- **Agent 1 — Delivery Simulation:** produces deterministic, per-resident outcomes for selected channels.
- **Agent 2 — Risk Analysis:** analyzes technical gaps and assigns risk priorities.
- **Agent 3 — Policy & Accessibility:** assesses simulated usability/actionability and separately flags Authorization and Privacy questions.
- **Agent 4 — Recovery Planning:** proposes feasible alternative assignments, reruns them under identical conditions and explains the chosen plan.

Typed interfaces, a scenario/data layer, `pipeline.py`, `recovery_runtime.py`, metrics, tests and reporting connect these components. **ITU-T Y.3172 (2019)** §§3.2.5–3.2.6, 7.5 and 8.1–8.2 provide a *conceptual architectural comparison* for pipeline, orchestration and sandbox concepts. This prototype does **not** implement Y.3172's telecom-network ML pipeline, MLFO, IMT-2020 interfaces or formal ML sandbox. Standards conformance is **Not Assessed**. See `docs/step4/maymona_standards_mapping.md`.

## 4. Mapping to ITU AI Readiness Report 2.0

The ITU's *AI Ready — Analysis Towards a Standardized Readiness Framework*, **Report 2.0 (January 2026)**, provides analytical context rather than a certification scheme for this prototype. LastMile demonstrates a **project-level qualitative mapping** to social inclusion (accessibility/connectivity), human-supervised planning (stage/channel selection), synthetic data governance, controlled testing and cross-domain emergency-communication considerations. It does **not** demonstrate national readiness, representative population measurements, real-world infrastructure capacity, trained-model performance or end-user usability validation. See `docs/step4/maymona_standards_mapping.md` and `docs/step4/maymona_claims_sources.md`.

## 5. Local Policies, Standards and Knowledge Resources

The frozen source registry documents **five source-metadata records (SRC-01–SRC-05)**: OASIS **CAP 1.2**, **ITU-T Y.3172**, **UAE-Alert TS FS 001 v2.0**, the **UAE National Policy for Digital Accessibility**, and **UAE Federal Decree-Law No. 45/2021** on personal data protection. CAP is **advisory context**, not a pass/fail validator. **CH01 SMS is not UAE Cell Broadcast**. Authorization and Privacy are separately labeled **scenario-based reviews**, not legal approval or compliance findings; applicable legislation and implementation obligations still need qualified review.

The repository's current knowledge resources provide a fixed warning fixture, channel-actionability documentation and **source-metadata lookup**. They do **not** implement full-text policy retrieval, vector search, RAG or an independently demonstrated ITU-hosted knowledge base. This is a documented limitation relevant to future work. Evidence: `docs/step4/maymona_kb_inventory.md` and `docs/step4/maymona_claims_sources.md`.

## 6. Evaluation Scenario — Technical and Policy

Cumulative event stages are: **T+00** baseline; **T+02** SMS outage conditions for designated Zone B residents; **T+04** additional modeled voice/signage accessibility barriers; and **T+06** hypothetical Authorization/Privacy review questions. A selected stage is a **fresh snapshot**, not a sequence of actual messages sent. SHA-256-based deterministic assumptions support reproducible timing/failure results. P0 and all feasible recovery alternatives are evaluated on the **same residents, stage, warning and enabled channels**.

Principal KPIs are **Estimated Reach** (unique residents with selected `Delivered`/`Delayed` attempts), **Effective Warning Coverage** (timely, actionable and simulation-usable selected warnings), **Recovery Improvement** (change in effective coverage, percentage points), and **Unresolved Critical Cases** (unique residents with unresolved HIGH technical priority). Missing evidence of usability is **not** evidence that a resident failed to understand the warning.

To reproduce the reviewed scenario from the repository root:

```powershell
python demo/run_demo.py --stage T+02
```

The run produces `demo_output/dashboard.html` and `demo_output/report.md`. **Ethar:** 10/10 scenario tests passed. **Salma:** 5/5 plan-comparison tests passed. **Full local suite:** 147/147 tests passed in **15.309 seconds**. The T+02 demo completed successfully using all five enabled channels. GitHub's displayed PR checks were green; access to that private PR must be granted for independent review.

## 7. Evaluation Findings, Uncertainty and Trade-offs

**Verified synthetic snapshot:** T+02:00, all five channels enabled.

| Metric | Baseline P0 | Selected recovery P3 |
|---|---:|---:|
| Estimated Reach | 722 / 1,000 | 942 / 1,000 |
| Effective Warning Coverage | 0 / 1,000 | 366 / 1,000 |
| Unresolved Critical Cases | 278 | 58 |

**Recovery Improvement:** **+36.6 percentage points** in simulated Effective Warning Coverage; the selected plan is **P3**. This also represents **+220** people in Estimated Reach and **220 fewer** unresolved critical technical cases for the verified snapshot. **P1/P2** were tested but did not improve confirmed effective coverage in this run; see `docs/step4/salma_recovery_evaluation.md` and the generated report for actual candidate-level results.

The zero confirmed effective-coverage result under P0 **does not** imply zero technical deliveries or prove any lack of comprehension. It reflects evidence requirements for actionable, usable selected warnings within this model. More generally, the recommended plan need not maximize every KPI; some scenarios reveal technical-reach versus verified-effective-coverage trade-offs. The prototype does not verify multipart-SMS completeness, voice playback completion, real end-user comprehension, telecom performance or actual digital-signage usability.

## 8. Identified Domain Policy and Standards Gaps

- **G01 — Accessibility/usability evidence (Review Required):** modeled person/channel suitability is not a disability-inclusive field or assistive-technology usability study. International context: **UNDRR 2023** disability-and-disasters survey and **U.S. DOJ** guidance on accessible emergency alerts. These sources are illustrative, not UAE deployment evidence.
- **G02 — Cross-channel interoperability (Review Required):** fixed Arabic representations do not establish live CAP exchange, telecom interoperability, complete multipart-SMS receipt or voice playback verification. International context: **OASIS CAP 1.2** and **WMO Early Warnings for All**.
- **G03 — Authorization, privacy and data minimization (Review Required):** synthetic resident records avoid operational personal data, but real deployment would need verified warning authority, applicable legal basis, security, retention and privacy governance. Context: **UAE Federal Decree-Law No. 45/2021** and ITU AI Readiness Report 2.0.

These are documented **evaluation and evidence gaps**, not findings of legal violations or formal standards nonconformance. Detailed references and limitations appear in `docs/step4/maymona_policy_gaps.md` and `docs/step4/maymona_claims_sources.md`.

---

**Submission checks remaining:** Confirm judges can access the repository and knowledge resources; transfer this text into the [official ITU technical-report template](https://s41721.pcdn.co/wp-content/uploads/2022/06/AI-for-Good-Sandbox-Hackathon-submission-template.docx), check the final document is **no more than five pages**, and obtain team review of citations and claims. This reviewed Markdown is **not yet the final ITU-formatted submission**.

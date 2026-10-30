# LastMile AI — Technical Report (DRAFT)

**AI-Powered Multi-Agent Emergency Communication & Resilience System**

**Event:** ITU AI for Good Lab Hackathon — United Arab Emirates  
**Team:** LastMile AI  
**Status:** Working Draft — Not Final Submission  
**Repository:** [Insert verified GitHub URL]  
**Knowledge Base:** [Insert verified KB link/access instructions]

*Submission note: Transfer this draft into the official ITU technical-report template. Maximum length: 5 pages. Replace bracketed fields following team review.*

## 1. Short Introduction to the Agentic AI Solution

LastMile AI is an offline, pre-event decision-support prototype designed to evaluate whether emergency warnings can reach residents, be usable under their accessibility and connectivity circumstances, and convey sufficient protective instructions.

The system compares a standard baseline warning-delivery plan (P0) against up to three tested accessibility-aware recovery plans (P1–P3).

It coordinates four agents: Delivery Simulation, Risk Analysis, Policy & Accessibility, and Recovery Planning. Their results feed into a reproducible HTML dashboard and Markdown report.

The prototype does not send operational emergency warnings or make actual deployment decisions.

## 2. Description and Requirements of the Use Case

The use case models a fictional flash-flood emergency in Al Wadi District using a synthetic dataset of 1,000 residents across Zones A, B and C.

Resident profiles include hearing and visual accessibility needs, weak mobile coverage, limited internet connectivity, age-related factors and channel availability.

The planner selects one cumulative stage — T+00, T+02, T+04 or T+06 — and enables at least one of five warning channels:

- CH01 — SMS
- CH02 — Mobile App
- CH03 — Automated Voice Call
- CH04 — Public Sirens
- CH05 — Digital Signage

The Arabic warning is fixed across stages and plans. The MVP prioritizes selecting suitable communication channels rather than rewriting or personalizing warning content.

**Core technical requirements**

- Evaluate technical delivery using Delivered, Delayed, Failed and Unavailable.
- Preserve identical scenario conditions across baseline and recovery comparisons.
- Distinguish technical delivery from accessibility and actionable content.
- Test recovery candidates using actual simulated outcomes.
- Document unresolved cases, recommendations and evidence references.

Public Sirens remain alert-only and cannot independently establish Effective Warning Coverage.

## 3. Solution Architecture and Mapping to ITU-T Y.3172

LastMile AI uses four coordinated modules:

**Agent 1 — Delivery Simulation:** Models selected-channel warning delivery and timing using deterministic rules.

**Agent 2 — Risk Analysis:** Identifies affected residents, evaluates technical delivery risks and assigns HIGH, MEDIUM or LOW priority.

**Agent 3 — Policy & Accessibility:** Evaluates whether the warning format is usable, whether protective instructions are sufficient, and whether Authorization or Privacy questions require review.

**Agent 4 — Recovery Planning:** Proposes alternative channel assignments, tests candidate plans under identical conditions, and recommends a feasible recovery plan.

The integration runtime coordinates the agents and calculates KPIs using actual simulation results.

The architecture is conceptually related to ITU-T Y.3172 through data preparation, workflow orchestration, evaluation, controlled experimentation and feedback.

**This is an architectural mapping, not a claim of formal ITU-T Y.3172 conformance.**

[Maymona: Insert verified mappings to specific Y.3172 concepts, supporting references and identified limitations.]

## 4. Mapping to ITU AI Readiness Framework 2.0

The prototype addresses selected AI-readiness considerations:

**Social Inclusion:** Explicit consideration of disability-related access barriers and connectivity disadvantages.

**Human Supervision:** Planning decisions remain under human control through stage and channel selection.

**Data Governance:** Synthetic resident data is used instead of operational personal records.

**Domain Integration:** Technical warning delivery, accessibility and policy considerations are assessed in a coordinated workflow.

**Responsible Evaluation:** Reproducible scenarios, documented assumptions and evidence-based uncertainty are preferred over unsupported success claims.

This constitutes a preliminary project-level mapping, not a national AI-readiness assessment.

[Maymona: Insert validated framework-dimension mapping and source references.]

## 5. Mapping to Local Policies and Standards

The current project references include:

- CAP 1.2 — emergency alert structure and information guidance.
- ITU-T Y.3172 — architecture-related reference.
- UAE mobile early-warning and Cell Broadcast documentation.
- UAE digital-accessibility policies.
- UAE personal data-protection legislation.

CAP is used for advisory explanations only. The prototype is not an automatic CAP compliance validator.

SMS (CH01) must not be confused with UAE Cell Broadcast infrastructure.

Authorization and Privacy are separate scenario-based assessments. Their outputs do not constitute legal approval or certification.

The current knowledge resources include a structured source registry, a fixed Arabic warning fixture and documented channel-actionability rules.

A fully vectorized, queryable knowledge base must not be claimed unless independently demonstrated.

[Maymona: Add verified sources, claim-to-evidence mappings, available retrieval demonstrations and unresolved policy questions.]

## 6. Evaluation Scenario — Technical and Policy

The simulation uses four cumulative event stages:

**T+00:** Initial emergency warning scenario.

**T+02:** EV01 — SMS outage conditions affect designated residents in Zone B.

**T+04:** EV02 — Additional accessibility barriers affect selected Voice Call and Digital Signage cases.

**T+06:** EV03 — Hypothetical Authorization and Privacy review questions arise; no external communication channel is activated.

The delivery model uses deterministic SHA-256-based timing and failure assumptions to enable reproducibility.

For each selected stage, the baseline and recovery plans are evaluated using identical resident profiles, warning content and scenario conditions.

**Main KPIs**

1. Estimated Reach — residents with selected technical arrivals marked Delivered or Delayed.
2. Effective Warning Coverage — residents with timely, actionable, individually usable selected warnings.
3. Recovery Improvement — improvement in effective coverage, measured in percentage points.
4. Unresolved Critical Cases — unique residents with unresolved HIGH technical risk.

The system also supports group-level accessibility analysis, channel-performance breakdowns, policy review indicators and decision traceability.

**Reproducible demonstration**

From the project repository root:

`python demo/run_demo.py --stage T+02`

Expected generated files:

- `demo_output/dashboard.html`
- `demo_output/report.md`

These outputs are generated from the integrated simulation.

[Ethar: Confirm scenario reproducibility and boundary-validation results.]

[Salma: Confirm final P0–P3 comparison, recovery selection and trade-offs.]

[Sereen: Insert the verified run results and final passing-test count after team review.]

## 7. Evaluation Findings, Uncertainty and Trade-offs

**Final verified results:** [Insert approved baseline-versus-recovery results table.]

The recommended recovery plan does not necessarily maximize every metric. A plan may improve confirmed effective coverage while reducing total technical reach.

Missing evidence about SMS message completeness, voice playback completion or individual format usability must be identified for review rather than treated as confirmed success.

A zero effective-coverage result does not prove that residents failed to receive or understand the warning. It means the specified evidence requirements for confirmed coverage were not met within the model.

**Limitations**

- All residents, event conditions and network assumptions are synthetic.
- No operational emergency messages are transmitted.
- Actual human comprehension is not measured.
- Voice TTS playback completion is not independently established.
- Real-world telecommunications performance is not validated.
- No automatic legal or CAP compliance certification is provided.

The prototype supports pre-event communication planning and controlled scenario evaluation, not live emergency response.

## 8. Identified Policy and Standards Gaps

[Maymona: Insert 2–3 verified, domain-specific policy or standards gaps with supporting evidence and global examples.]

Topics to investigate, not yet confirmed findings, include:

- Accessibility evidence across multiple emergency-warning formats.
- Alternative communication options during connectivity disruptions.
- Authorization and privacy traceability when external communication channels are considered.

Each final gap must distinguish the documented issue, applicable source, possible international comparison, and remaining uncertainty.

## Final Submission Verification

Before submission, confirm:

- GitHub repository accessibility and verified URL.
- Knowledge-base location, supported capabilities and access instructions.
- Final evidence-backed mapping to ITU-T Y.3172 and AI Readiness 2.0.
- Scenario validation and reviewed P0–P3 results.
- Passing automated tests and reproducible demonstration.
- Final policy and standards references.
- Team review of the technical claims.
- Maximum five-page length in the official ITU template.
- Optional demonstration video link, if produced.

**Status: Draft pending team evidence review and final integration.**
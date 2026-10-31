# LastMile AI — Step 4 Policy, Standards & Accessibility Gaps

**Owner:** Maymona · **Review snapshot:** 30 October 2026 · **Basis:** approved Step 1, Sirin-approved Arabic Step 2 fixture, integrated Step 3 repository.  
**Scope:** exactly three *bounded gaps* for the warning sector and possible future deployment. **Not legal findings, compliance certificates, or measured deficits of a real UAE warning authority.**

## How to read the findings

- **Observed in repository** = what the supplied program/documentation actually demonstrates or omits.
- **External context** = official documents and illustrative international practice; not binding on a fictional test unless independently shown applicable.
- **Review Required** = missing evidence or a potential implementation/legal question; it is **not** a failure verdict.
- The synthetic scenario uses **1,000 fictional residents**, the fixed Arabic warning, five existing simulated channels, and no real transmission or personal records. Do not derive population-level or legal conclusions from its results.

## G01 — Inclusive, actionable warnings versus technical receipt

**Sector question.** Does an alert arrive *in a format that each person can use*, carrying information sufficient to take protective action, including when network, hearing, vision or device constraints interact?

**External, verifiable context.**

1. **UNDRR 2023 Global Survey on Persons with Disabilities and Disasters** (report page, sections *The Survey*, *Disaster information in accessible formats*, *DRR plans to address specific needs*): the survey received **6,342 responses from 132 countries**; only **8% (488)** of respondents reported that their *local* disaster-risk-reduction plans addressed the specific needs of persons with disabilities. These are **survey responses**, not statistics for the UAE or our synthetic residents. [UNDRR official report page](https://www.undrr.org/report/2023-gobal-survey-report-on-persons-with-disabilities-and-disasters).
2. **U.S. Department of Justice, ADA.gov, Emergency Planning** (section *Emergency Alerts*): an illustrative public-sector practice is to combine audible and visible alerts and multiple electronic methods, recognizing that sirens or visual cues alone may be inaccessible to particular users. **U.S. guidance is an international example, not a UAE legal requirement.** [ADA.gov guidance](https://www.ada.gov/topics/emergency-planning/).
3. **UAE National Policy for Digital Accessibility**, March 2024, Articles 2–3, addresses inclusive access to covered digital services and service-specific applicability. Do not infer a blanket legal obligation for all five channels. [TDRA official policy](https://dgov.tdra.gov.ae/en/publications/national-digital-accessibility-policy).
4. **ITU AI Readiness Report 2.0**, January 2026, *Human Interface* (PDF pp. 25–26 / printed pp. 23–24), considers local language, interaction channels and usability for people with special needs. It is an **analysis framework**, not a certification. [ITU PDF](https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf).

**Actual LastMile evidence.** `lastmile_ai/agents/policy_accessibility.py` assesses selected arrivals using resident-level `voice_usable` / `signage_readable` and separate optional format evidence; `evaluation.py` evaluates the *fixed* rendered text against hazard, area and protective-instruction markers. `docs/channel_actionability.md` states **CH04 sirens are alert-only**. Missing SMS completion / Arabic TTS playback / personal text-app usability evidence is not treated as confirmed actionability. These are **simulation proxies**, not observed understanding.

**Gap / status: Review Required.** No direct user studies, screen-reader checks on actual devices, measured user comprehension, validated Arabic TTS listening duration, or proof of accessible emergency actions in real conditions. A lack of modeled evidence is **not evidence of an individual failing to understand**.

**Future evidence to close (not Step 4 implementation):** co-designed disability-inclusive user tests; real devices and assistive technologies; clearly documented signal-to-instruction path; Arabic presentation/playback verification; reproducible acceptance thresholds for all relevant formats. **Do not alter Agent 3 under Step 4 core freeze.**

## G02 — Cross-channel warning interoperability and complete-instruction evidence

**Sector question.** How do official warning fields, authorization and protective instructions remain consistent across SMS, app, voice, sirens and public signage when media have different constraints?

**External, verifiable context.**

1. **OASIS CAP 1.2**, §3.2 *Data Dictionary*, provides a standardized *message structure*; it does not prove complete delivery on individual devices. [OASIS CAP 1.2](https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html).
2. **WMO, Common Alerting Protocol**, explains that CAP facilitates consistent warnings shared across multiple media. This is a **global implementation reference**, not evidence that our system exchanges actual CAP messages. [WMO CAP page](https://public.wmo.int/activities/common-alerting-protocol-cap).
3. **WMO Early Warnings for All Executive Action Plan 2023–2027**, section *Warning dissemination and communication*, highlights trusted dissemination channels and actionable warning messages; its four pillars extend beyond our pre-event simulator. [WMO Bulletin overview](https://wmo.int/resources/wmo-bulletin/wmo-bulletin-vol-72-1-2023/overview-of-early-warnings-all-executive-action-plan-2023-2027).
4. **TDRA TS FS 001 v2.0 (2019)** specifies **Cell Broadcast / UAE-Alert** context; **CH01 remains SMS and is not that protocol**. [Original TDRA specification](https://tdra.gov.ae/en/about/tdra-sectors/telecommunication/the-technology-development-affairs/-/media/1ABB576C428A4BAC8E777204233D5033.ashx).

**Actual LastMile evidence.** `lastmile_ai/knowledge/warning_fixture.json` fixes *Arabic* canonical and channel-specific renderings; `evaluation.py` checks documented information elements and conservatively flags SMS complete-receipt and voice playback unknowns. `lastmile_ai/recovery_runtime.py` compares permitted alternatives under shared simulated conditions. The project **does not** implement a CAP XML validator, 3GPP/Cell Broadcast stack, live alert operator or confirmed channel-level receipts from real networks.

**Gap / status: Review Required.** No approved real-service specification mapping structured alerts to channel encodings, screen dimensions, speech pacing/complete listening, multipart SMS reassembly or cross-operator acknowledgement. There is no evidence of network/protocol interoperability conformance or a real authorized broadcasting workflow.

**Future evidence to close:** authority-approved mapping from warning fields to each channel; segment-completeness and spoken-instruction tests; issuer authentication and provenance for a real environment; proof of consistent instructions when media limits apply. **Keep these as future integration questions, not new MVP channels.**

## G03 — Data minimization, privacy and authorization for accessibility-sensitive information

**Sector question.** If a real planner wanted to route warnings based on a person's accessibility-related needs, who is authorized to process that information, on what applicable basis and under what security/retention limits?

**External, verifiable context.**

1. **UAE Federal Decree-Law No. 45 of 2021 on Personal Data Protection**, with Article 2 scope/exceptions and relevant processing provisions (see source `SRC-05`). The **official UAE government overview** describes privacy, processing controls, data-subject rights and cross-border transfer provisions. [Government overview](https://u.ae/en/about-the-uae/digital-uae/data/data-protection-laws); [official legislation locator](https://uaelegislation.gov.ae/en/legislations/1972). The latter gave an automated **403** in the earlier verification; a supplied local PDF is **not proof of the latest amended text**. Application to particular authorities/providers must be reviewed by qualified people.
2. **ITU AI Readiness Report 2.0** (PDF pp. 14–17, sections *Data* and *AI Policy*) addresses data governance, safeguards, quality, and regulatory frameworks as readiness considerations, **not a project's compliance score**. [ITU official report](https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf).
3. **WMO Early Warnings for All** discusses institutional responsibilities for public warning procedures. It is contextual governance guidance, not a decision that external operators in our fictional scenario are authorized. [WMO overview](https://wmo.int/resources/wmo-bulletin/wmo-bulletin-vol-72-1-2023/overview-of-early-warnings-all-executive-action-plan-2023-2027).

**Actual LastMile evidence.** The dataset is explicitly **synthetic**. `lastmile_ai/agents/policy_accessibility.py` emits separate Authorization and Privacy findings and marks the **hypothetical external EV03 route** `Review Required` without activating it, exporting real data or automatically blocking the five internal channels. Its `SRC-05` citation links to a source *record*; it does **not** fetch or apply a complete legal text.

**Gap / status: Review Required.** No validated authorization basis for a real provider, sensitive-data inventory, formal retention schedule, deployment data-flow agreements, or qualified legal applicability opinion; amendments and exceptions were not established as current in a live official legislative text review.

**Future evidence to close:** written purpose/legal-basis assessment with authority and jurisdiction, data minimization, retention/deletion design, controls over any outside sharing, security and human-oversight review before real resident data or operators are involved. **Do not assert lawful, unlawful or policy compliant.**

## Concise gap decision matrix

| Gap ID | Demonstrated prototype safeguard | Missing evidence | Status | Who could resolve it later? |
|---|---|---|---|---|
| G01 | Resident/channel usability checks, Arabic fixed content, alert-only siren | Real accessibility/usability/comprehension testing | **Review Required** | Disability stakeholders + service designers + field evaluators |
| G02 | Five fixed representations; deterministic source-aware content proxy | Actual multi-channel protocol/format mapping, complete receipts, operator authorization | **Review Required** | Warning authority + telecom/media integrators |
| G03 | Synthetic records and separate Authorization/Privacy reviews | Applicable real-data legal basis, governance/security evidence and current law verification | **Review Required** | Authorized privacy/legal and warning-system owners |

## Reproducible desk review (no repository edits)

From the **extracted project root**, inspect the evidence with commands such as:

```bash
python -c "import json; f=json.load(open('lastmile_ai/knowledge/warning_fixture.json',encoding='utf-8')); print(f['warning']['language'], sorted(f['approved_channel_renderings']))"
python -c "import json; r=json.load(open('lastmile_ai/knowledge/sources_registry.json',encoding='utf-8')); print([s['id'] for s in r['sources']])"
python -m unittest discover -s tests -p 'test_*.py'
```

Expected first two outputs: `ar ['CH01', 'CH02', 'CH03', 'CH04', 'CH05']` and `['SRC-01', 'SRC-02', 'SRC-03', 'SRC-04', 'SRC-05']`. The tests check the current code's behaviors; they do **not** close these real-world evidence gaps.

## Scope and source policy

This Step 4 file **references additional public international examples** (UNDRR, WMO, ADA.gov) for explanatory context. It **does not add entries** to the fixed five-source `sources_registry.json` or change the scope or code of Agents 1–4. Review date **30 October 2026**; retrieval is a documentation snapshot, not assurance that future regulation or deployments are unchanged.

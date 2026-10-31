# LastMile AI — Step 4 Claim-to-Evidence Traceability

**Owner:** Maymona · **Evidence snapshot:** 30 October 2026 · **Repository:** supplied integrated Step 3 ZIP · **Purpose:** transparent claims that judges can independently check.  
**Assessment labels:** `Demonstrated (synthetic/code)` = observable artifact/behavior; `Documented assumption` = fixed design assumption; `External context` = official external statement; `Review Required` = insufficient evidence for stronger interpretation. No numeric field-effectiveness, legal conformance or standard certification claim is made.

## 1. Claims backed by repository or official references

| ID | Exact bounded claim | Project proof (path → anchor) | Official / external supporting context | Finding and caution |
|---|---|---|---|---|
| **C01** | The MVP uses one fictional Al Wadi scenario, 1,000 synthetic residents and five CH01–CH05 channels. | `lastmile_ai/knowledge/warning_fixture.json` → `scenario`, `simulation_policy.channel_ids`; dataset `data/reference/LastMile_AI_Step1_Master_Dataset.xlsx` | Approved Step 1 Master | **Documented assumption** — not real warning coverage |
| **C02** | The same preapproved Arabic warning/representations are fixed across P0 and recovery alternatives. | `lastmile_ai/knowledge/warning_fixture.json` → `warning.language`, `warning.canonical_text`, `approved_channel_renderings` | Sirin-approved Step 2 | **Demonstrated fixture**, not language comprehension |
| **C03** | A siren is alert-only, not stand-alone actionable coverage. | `lastmile_ai/agents/evaluation.py` → `evaluate_content`, `ChannelID.PUBLIC_SIRENS`; `docs/channel_actionability.md` | Approved Step 1 | **Demonstrated rule**, not individual audibility |
| **C04** | Agent 3 examines person-level voice/signage format flags, rather than automatically rejecting impairment groups. | `lastmile_ai/agents/policy_accessibility.py` → `assess_agent3`, `person.voice_usable`, `person.signage_readable` | UAE accessibility policy `SRC-04` contextual | **Demonstrated code**, no real usability study |
| **C05** | SMS multipart completion and full Arabic TTS playback are not automatically proved by a delivery result. | `lastmile_ai/agents/evaluation.py` → `complete_rendering_received`, `audio_playback_completed`; `policy_accessibility.py` → `rendering_evidence` | Fixed Step 2 actionability requirements | **Demonstrated conservative logic**; no real message-segment receipt or recording test |
| **C06** | Fixed Arabic text is checked using hazard, affected area and protective-instruction markers. | `lastmile_ai/agents/evaluation.py` → `hazard`, `area`, `protective`, `ContentStatus` | ITU AI Readiness Report 2.0 *Human Interface*, PDF pp. 25–26 (analysis context) | **Demonstrated deterministic proxy**, not semantic AI verification, human understanding or a learned-model score |
| **C07** | Agent 3 emits distinct Authorization and Privacy assessments. | `lastmile_ai/agents/policy_accessibility.py` → `policies`, `PolicyFinding` | `SRC-05` UAE PDPL | **Demonstrated model**, not lawfulness certification |
| **C08** | At T+06, EV03 concerns a hypothetical outside route; it is flagged for review and not activated as a real channel. | `lastmile_ai/agents/policy_accessibility.py` → `ev03`, `PolicyCheckStatus.REVIEW_REQUIRED`; `agents/scenario_conditions.py` | Approved Step 1 Master | **Demonstrated rule**, not evidence of actual external sharing |
| **C09** | CAP 1.2 is advisory context and the system does not run an automated CAP conformance validator. | `lastmile_ai/agents/policy_accessibility.py` → `CAPAdvisory`; `knowledge/sources_registry.json` → `SRC-01` | [OASIS CAP 1.2 §3.2](https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html) | **Demonstrated bounded use**, no CAP pass/fail |
| **C10** | UAE-Alert TS FS 001 v2.0 concerns Cell Broadcast; CH01 is SMS. | `knowledge/sources_registry.json` → `SRC-03`; `docs/channel_actionability.md` | [TDRA TS FS 001](https://tdra.gov.ae/en/about/tdra-sectors/telecommunication/the-technology-development-affairs/-/media/1ABB576C428A4BAC8E777204233D5033.ashx) | **Documented distinction**, no Cell Broadcast/3GPP simulation |
| **C11** | Y.3172 describes network-ML pipeline and orchestration concepts; LastMile has an application workflow. | `lastmile_ai/pipeline.py`, `recovery_runtime.py`; `knowledge/sources_registry.json` → `SRC-02` | [ITU-T Y.3172 §§7–8](https://www.itu.int/rec/T-REC-Y.3172-201906-I/en) | **Conceptual analogy** — no Y.3172 conformance, MLFO or real IMT-2020 network |
| **C12** | Current project can look up five source **metadata records** but does not retrieve standard-document passages. | `knowledge/sources_registry.json` → `sources`; `agents/policy_accessibility.py` → `load_knowledge`; [repeatable command below] | None required to state inspected repository limit | **Demonstrated boundary** — not RAG, vector search or passage-level retrieval |
| **C13** | ITU *AI Ready* is officially titled **Report 2.0, January 2026**, and includes data governance, infrastructure, standards/sandbox and human-interface analysis. | `docs/step4/maymona_standards_mapping.md` | [ITU official PDF](https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf): cover PDF p. 1; framework PDF pp. 14–17; factors PDF pp. 19–20; interface PDF pp. 25–26 | **Verified external context** — report is **not** a mandatory project-specific compliance specification |
| **C14** | The project shows synthetic coverage/resilience evaluation, not national AI readiness or live-network performance. | `lastmile_ai/agents/delivery.py`, `agents/scenario_conditions.py`, `recovery_runtime.py`, `metrics.py` | ITU *AI Ready* Report 2.0, PDF pp. 14–17 | **Demonstrated scope only**, no national index or live network validation |
| **C15** | UAE National Policy for Digital Accessibility is relevant to accessible digital-service design, subject to applicability. | `knowledge/sources_registry.json` → `SRC-04`; `docs/channel_actionability.md` | [TDRA policy](https://dgov.tdra.gov.ae/en/publications/national-digital-accessibility-policy), Articles 2–3, March 2024 | **Official source context**; policy scope and technical compliance are **Review Required** |
| **C16** | Federal Decree-Law No. 45/2021 is a privacy governance reference, not an automatic decision on this scenario. | `knowledge/sources_registry.json` → `SRC-05`; `policy_accessibility.py` → `PolicyFinding` | [UAE government overview](https://u.ae/en/about-the-uae/digital-uae/data/data-protection-laws); [legislation locator](https://uaelegislation.gov.ae/en/legislations/1972) | **Official contextual overview**; legislation locator blocked automated access (403); current amendments/applicability **Review Required** |
| **C17** | WMO's Early Warnings for All presents warning dissemination and communication as one of **four pillars**. | `docs/step4/maymona_policy_gaps.md` → `G02` | [WMO Executive Action Plan overview](https://wmo.int/resources/wmo-bulletin/wmo-bulletin-vol-72-1-2023/overview-of-early-warnings-all-executive-action-plan-2023-2027), sections *Four pillars* / *Warning dissemination* | **External sector context**; LastMile does not implement an operational end-to-end EWS |
| **C18** | The UNDRR 2023 survey identifies persistent disability-inclusion concerns in disaster planning. | `docs/step4/maymona_policy_gaps.md` → `G01` | [UNDRR report page](https://www.undrr.org/report/2023-gobal-survey-report-on-persons-with-disabilities-and-disasters), *The Survey* and *DRR plans* sections: 6,342 responses / 132 countries; 8% reported their local plans address specific needs | **External survey finding**; sample is **not** UAE-specific nor evidence of our residents' outcomes |
| **C19** | International guidance illustrates using multiple accessible alert modalities rather than relying on sirens or visual cues alone. | `docs/step4/maymona_policy_gaps.md` → `G01` | [U.S. Department of Justice, Emergency Planning](https://www.ada.gov/topics/emergency-planning/), *Emergency Alerts* | **Illustrative international practice only**, not UAE legal applicability |
| **C20** | WMO identifies CAP as a format that supports consistent emergency communication across multiple media. | `docs/step4/maymona_policy_gaps.md` → `G02` | [WMO CAP overview](https://public.wmo.int/activities/common-alerting-protocol-cap) | **External standards context** — LastMile has not implemented real multi-channel CAP dispatch |

## 2. Evidence strength / unsupported-claim register

| Overstatement to avoid | Evidence needed before such a statement could be made | Current decision |
|---|---|---|
| “LastMile AI complies with ITU-T Y.3172 / CAP / ITU AI Readiness 2.0.” | Standard-specific conformance scope, independent normative assessment where applicable | **Not Assessed**; architecture-inspired/readiness mapping only |
| “The project proves warning comprehension or accessibility for real people.” | Representative disability-inclusive field studies and actual device testing | **Review Required** |
| “The platform has a source-document RAG Knowledge Base.” | Indexed licensed texts, passage provenance, retrieval implementation/evaluation | **Not implemented**; metadata only |
| “This proposed external channel is legally authorized / illegal.” | Qualified assessment of real authority, current applicable law and authorization | **Review Required** |
| “The prototype reached 90% of a real population or validated five live delivery networks.” | Real operational tests and confirmed measurements | **Not claimed**; only synthetic simulation |
| “All SMS segments and the complete TTS recording were heard merely because a warning arrived.” | Channel-specific completeness/playback evidence and user testing | **Not established** |

## 3. Reproducible evidence checks (read-only)

Execute from the **extracted Step 3 project root** (no pip installations required for the first two commands):

```bash
python -c "import json; p='lastmile_ai/knowledge/sources_registry.json'; r=json.load(open(p,encoding='utf-8')); q='accessibility'; hits=[s for s in r['sources'] if q in (' '.join(map(str,[s['title'],s['project_use'],s['agent_3_use']]))).lower()]; print([(s['id'],s['title'],s['official_url']) for s in hits])"
python -c "import json; f=json.load(open('lastmile_ai/knowledge/warning_fixture.json',encoding='utf-8')); print(f['warning']['language'],sorted(f['approved_channel_renderings']))"
python -m unittest discover -s tests -p 'test_*.py'
```

The registry lookup returns **metadata**, not verified quotations from source PDFs. The second command should print `ar ['CH01', 'CH02', 'CH03', 'CH04', 'CH05']`. The unittest command tests the supplied application code; it does **not** prove standards/legal compliance or any real-world warning results.

## 4. Checkpoint with Step 4 counterparts

- `maymona_kb_inventory.md`: verifies the **five frozen core references** and documents AI Readiness Report 2.0 as a **supplementary Step 4 source**, not an added registry entry. It records actual verification limitations.
- `maymona_standards_mapping.md`: maps Y.3172 and the January 2026 ITU report to named files/functions and calls out unimplemented standards-specific capabilities.
- `maymona_policy_gaps.md`: documents exactly **three** sector-level gaps `G01`–`G03` with primary and international illustrative sources.
- **No** core files, schemas, dataset, source registry, agent implementations, metrics or reports have been edited in Step 4.

**Documentation review date:** 2026-10-30. The official URLs are citation targets checked during this audit; URLs, versions, legal status and accessibility requirements may change. Questions involving current legislation and real service providers remain **Review Required**.

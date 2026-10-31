# LastMile AI — Step 4 Standards & AI Readiness Evidence Mapping

**Owner:** Maymona | **Review:** 30 October 2026 | **Baseline:** uploaded integrated Step 3 `LastMile-main (1)(3).zip` (read-only).

**Purpose:** auditable mapping of *actual code and documents* to relevant concepts in two ITU publications and the existing UAE accessibility/privacy references. **This is neither a compliance audit nor an ITU AI Readiness score/certification.** Only this new Step 4 documentation file is changed.

## 1. Source identity and precise citation convention

| Ref | Official document | Source anchor | Appropriate use |
|---|---|---|---|
| **Y3172** | ITU-T Recommendation **Y.3172 (06/2019)**, *Architectural framework for machine learning in future networks including IMT-2020* | [ITU recommendation](https://www.itu.int/rec/T-REC-Y.3172-201906-I/en); §§3.2.5–3.2.6 (ML pipeline, ML sandbox), §§7.5 and 8.1–8.2 (ML functionalities, high-level components) | Architecture **analogy**, not implementation of a network ML pipeline |
| **AIR2** | ITU, *AI Ready – Analysis Towards a Standardized Readiness Framework*, **Report 2.0, January 2026** | [Official 55-page PDF](https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf); PDF pp. 14–17 (basic framework/data), PDF pp. 19–20 (six factors), PDF pp. 24–26 (workflows/human interface) | Readiness **analysis lenses**, not mandatory project requirements |
| **ACCESS** | UAE National Policy for Digital Accessibility, March 2024 | [Official TDRA policy](https://dgov.tdra.gov.ae/en/publications/national-digital-accessibility-policy); Articles 2–3 | Accessibility principles **subject to applicability** |
| **PRIVACY** | UAE Federal Decree-Law No. 45/2021 | [Legislation locator](https://uaelegislation.gov.ae/en/legislations/1972); Articles 2, 4–5 | Privacy principles; live-page validation / amendments still **Review Required** |
| **CAP** | OASIS CAP v1.2 | [OASIS](https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html), §3.2 | Advisory warning structure, **not** CAP validator |

**Page rule:** PDF page numbers are counted from the cover (PDF p. 1). Printed report page numbers differ (for instance AIR2 *Human Interface* is printed pp. 23–24, PDF pp. 25–26). *Report 2.0* is evidenced directly by its January 2026 cover; the report's informational disclaimer refers separately to June 2025. It is a **Step 4 supplementary reference**, **not a sixth entry** in the frozen five-source Step 2 registry.

## 2. ITU-T Y.3172: architecture analogy versus actual implementation

| Relevant provision | Concrete repository evidence | What we can truthfully say | Gap / decision |
|---|---|---|---|
| **§3.2.5** ML pipeline definition; **§8.1** ML pipeline nodes | `lastmile_ai/pipeline.py` (`run_baseline`), `lastmile_ai/runtime.py`, `lastmile_ai/agents/{delivery,risk,policy_accessibility,recovery}.py` | Sequenced four-agent **application** evaluation with typed data handoffs | **Conceptual only:** no evidence of Y.3172 network-ML source/collector/preprocessor/model/distributor topology, deployed ML model lifecycle or telecommunications network underlay |
| **§7.5 / §8.1–8.2** ML management/orchestration and high-level architecture | `lastmile_ai/recovery_runtime.py` (`run_integrated_recovery`); `lastmile_ai/pipeline.py` | Deterministic orchestration of baseline P0 and evaluated alternatives | **Partial analogy**, not implemented Y.3172 MLFO, network management integration or IMT-2020 interfaces |
| **§3.2.6 / §8.1** ML sandbox | `lastmile_ai/agents/scenario_conditions.py`, `lastmile_ai/agents/delivery.py`; synthetic dataset under `data/reference/` | An **isolated synthetic warning scenario** allows repeatable pre-emergency testing | This is an application *simulation environment*, **not evidence of a formal Y.3172 ML sandbox subsystem** |
| **§7.3 / §8.2** interface-related concepts | `lastmile_ai/schemas.py`, `docs/agent_contracts.md` | Agent inputs and outputs are specified within this codebase | No Y.3172 reference-point protocol conformance or cross-operator interoperability demonstration |

**Y.3172 conclusion:** *architecture-inspired / conceptual mapping only*; use **Not Assessed** for standards conformity, not **Compliant**.

## 3. ITU AI Readiness Report 2.0: project evidence and limitations

| AI Readiness Report 2.0 anchor | Actual LastMile evidence | Demonstrated | Missing / status |
|---|---|---|---|
| **Basic framework: Data** (PDF pp. 14, 16–17): quality, representativeness, governance, interoperability | `data/reference/LastMile_AI_Step1_Master_Dataset.xlsx`; `lastmile_ai/data/resident_adapter.py`; `tests/test_dataset.py` | Synthetic 1,000-person scenario, deterministic records, input checks | No real-population representativeness validation, discrimination audit, or deployed data-governance assessment — **Partial / Review Required** |
| **Digital Infrastructure** (PDF pp. 14, 17): network coverage, devices, computing | `lastmile_ai/agents/scenario_conditions.py`, `delivery.py` | Modeled Zone B SMS outage, weak coverage and limited internet; five channels | No operator network measurements, national infrastructure score, device usability testing — **Simulation only** |
| **Digital Skills / Innovation Ecosystem** (PDF p. 15) | `README.md`, Python project/tests, ITU-T source registry | Reproducible prototype and documented references | National skills levels, investments, standards participation not measured — **Not Assessed** |
| **AI Policy** (PDF p. 15) / **six factors: Standards, Sandbox** (PDF pp. 19–20) | `lastmile_ai/knowledge/sources_registry.json`; `policy_accessibility.py`; documented synthetic scenario | Source-aware, advisory privacy/authorization outcomes and sandbox-style testing | Neither legal certification nor a national/regional readiness index — **Partial** |
| **Dimension 5: Level of Integration of AI in Workflows** (PDF pp. 24–25) | `lastmile_ai/pipeline.py`, `recovery_runtime.py`, `report.py`; `tests/test_agent4_runtime.py` | Actual integrated stages; baseline/recovery comparison and generated report | No real-service time savings, deployment scale, or externally measured impact — **Prototype evidence only** |
| **Dimension 6: Human Interface** (PDF pp. 25–26): local language, special needs, multiple interaction channels | `lastmile_ai/knowledge/warning_fixture.json` (Arabic); `docs/channel_actionability.md`; `lastmile_ai/agents/evaluation.py`, `policy_accessibility.py` | Fixed Arabic warning, app RTL *assumption*, channel-specific actionability, `voice_usable` and `signage_readable` proxies | No independent screen-reader testing, confirmed Arabic TTS playback duration, field usability/comprehension study — **Partial / Review Required** |
| **Contextualization and Regional Impact** (PDF pp. 23–24) | Fictional Al Wadi UAE-inspired scenario, approved Arabic fixture | Regional language and fictional UAE-relevant setting | Real local dataset, stakeholder validation, actual regional benefit not established — **Conceptual only** |

**Readiness conclusion:** this is a **qualitative mapping to selected analytical dimensions**, not a score against all dimensions; country-level indicators cannot be inferred from one prototype.

## 4. Accessibility, privacy and warning standards mapping

| Reference and concept | Code / evidence | Supported statement | Must not claim |
|---|---|---|---|
| **ACCESS Articles 2–3** inclusive accessibility and scoped applicability | `policy_accessibility.py` checks channel-specific person-level flags; `docs/channel_actionability.md` describes formats | Synthetic detection of some modeled accessibility barriers and unknown usability | WCAG certification, proof of accessibility for all people, or universal legal applicability |
| **PRIVACY Articles 2, 4–5** scope/exemptions and data protection principles | `policy_accessibility.py` produces privacy review separate from authorization; EV03 hypothetical external channel review | Scenario-level risk flag and source reference | A definitive interpretation of UAE law, lawful/unlawful conclusion, or actual-person data assessment |
| **CAP v1.2 §3.2** alert structure | `policy_accessibility.py` CAP advisory; source registry `SRC-01`; fixed warning JSON | Structured, traceable advisory context | CAP XML validation, conformance pass/fail |
| **UAE-Alert TS FS 001 v2.0** Cell Broadcast context | `sources_registry.json`, `docs/channel_actionability.md` | Explicit distinction between UAE Cell Broadcast and simulated **CH01 SMS** | Assuming broadcast standard is an SMS specification or adding CH06 |

## 5. Evidence quality: three example audit trails

1. **Arabic accessible warning (bounded):** AIR2 PDF pp. 25–26, Dimension 6 → `lastmile_ai/knowledge/warning_fixture.json` (Arabic channel texts) → `docs/channel_actionability.md` → `policy_accessibility.py`. **Inference:** language choice and simulated accessibility checks exist; **unknown:** actual resident comprehension and real device accessibility.
2. **Resilience to a network outage (bounded):** AIR2 PDF pp. 14, 17 (connectivity) → `scenario_conditions.py` and `delivery.py` → `recovery_runtime.py`. **Inference:** replayable simulated outage and candidate evaluation; **unknown:** real telecom performance.
3. **ML orchestration (analogy):** Y.3172 §§7.5, 8.1–8.2 → `pipeline.py` / `recovery_runtime.py`. **Inference:** sequence of software agents; **unknown:** existence of the standard's MLFO or underlay networking components.

## 6. Findings requiring review before any stronger claim

- **Review Required:** distinguish deterministic rule-based simulation and software agents from a trained/deployed **ML model**. Do not infer Y.3172 conformance merely because the product name includes AI.
- **Review Required:** no independent human participant or screen reader evaluation; do not report quantitative accessibility success beyond model proxies.
- **Review Required:** source registry is **metadata lookup**, not indexed passage retrieval; citation identifiers do not prove the agent fetched full official text.
- **Review Required:** UAE legal-policy applicability, latest amendments and UAE-Alert newer editions require an authorized human source review.
- **Review Required:** Arabic TTS audio creation and recorded play duration are not evidenced as operational outputs.

## 7. How to reproduce this documentation audit

From the extracted Step 3 project root, inspect the referenced files under `lastmile_ai/`, `docs/`, `tests/`, and `data/reference/`. Official references and anchors are in §1. The auditable assertion here is **file/function existence and bounded semantics**, not automatic compliance. No framework-scoring script, source-text RAG, or standardized network interface was added. This document is the **only** deliverable created in this stage.

**Next stages:** update `maymona_policy_gaps.md` with externally sourced gap examples, then synchronize `maymona_claims_sources.md`. The already verified `maymona_kb_inventory.md` remains unchanged.

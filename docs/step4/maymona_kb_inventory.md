# Step 4 — Knowledge Base & Source Inventory (Maymona)

**Baseline:** `LastMile-main (1)(3).zip` / identical contents to `LastMile-integration-step3-review(3).zip`; approved Step 1 and Sirin-approved Step 2 Arabic fixture. **Audit date:** 2026-10-30. **Scope:** read-only review of current repository. This file is documentation, not a core-file update.

## 1. What actually exists

- `lastmile_ai/knowledge/sources_registry.json`: version `1.1.0`, 5 source metadata records (IDs SRC-01–SRC-05). Includes URLs, version, relevant sections, usage/limitations; **no downloaded passages, embedded vectors, document text index or retrieval corpus**.
- `lastmile_ai/knowledge/warning_fixture.json`: approved Arabic fixed Al Wadi simulation message, fixed channel representations and scenario assumptions. **Not a standards knowledge database.**
- `docs/channel_actionability.md`: documented channel content and review rules.
- `lastmile_ai/agents/policy_accessibility.py`: loads the registry and fixed warning JSON; uses `SRC-01` advisory and `SRC-05` as evidence labels in findings; **does not search official document contents**.
- `lastmile_ai/agents/evaluation.py`: fixed Arabic lexical content-sufficiency proxy; **not CAP certification or proof of comprehension**.

## 2. Official source inventory

The **access-date field below records this review attempt**, not independent verification of every document's current legal force. The original registry remains unchanged.

| ID | Source | Issuer | Recorded edition | Original URL and access date | Verification outcome |
|---|---|---|---|---|---|
| SRC-01 | Common Alerting Protocol (CAP) Version 1.2 | OASIS Emergency Management Technical Committee | 1.2 | [2026-10-30](https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2-os.html) | Public OASIS standard opened; title/version confirmed |
| SRC-02 | ITU-T Y.3172 — Architectural framework for machine learning in future networks including IMT-2020 | International Telecommunication Union — Telecommunication Standardization Sector (ITU-T) | Y.3172 (06/2019) | [2026-10-30](https://www.itu.int/rec/T-REC-Y.3172-201906-I/en) | ITU Recommendation webpage opened; Y.3172 06/2019 in force |
| SRC-03 | TS FS 001 — Enabling Cell Broadcast for National Public Warning Service (UAE-Alert) | Telecommunications Regulatory Authority (TRA), now Telecommunications and Digital Government Regulatory Authority (TDRA), UAE | 2.0 | [2026-10-30](https://tdra.gov.ae/en/about/tdra-sectors/telecommunication/the-technology-development-affairs/-/media/1ABB576C428A4BAC8E777204233D5033.ashx) | Official PDF opened; title/version confirmed from cover page |
| SRC-04 | UAE National Policy for Digital Accessibility | Telecommunications and Digital Government Regulatory Authority (TDRA), UAE | March 2024 issue | [2026-10-30](https://dgov.tdra.gov.ae/en/publications/national-digital-accessibility-policy) | **Full official 20-page PDF retrieved and inspected**, [English PDF](https://dgov.tdra.gov.ae/-/media/dgov/pdfs/publications/national-digital-accessibility-policy-en.pdf); Articles 2–3 and age 60+ definition verified; applicability to a real service still conditional |
| SRC-05 | Federal Decree-Law No. (45) of 2021 Concerning the Protection of Personal Data | United Arab Emirates Government | No. 45 of 2021 | [2026-10-30](https://uaelegislation.gov.ae/en/legislations/1972) | Official legislation webpage and its `/download` returned HTTP 403; **an already-provided PDF copy of the law was inspected locally** (cover, title, Article 1). Its currency, amendments and legal applicability **not verified** |

### What these sources can actually support and what remains open

| ID | Supportable contextual claim | Open question / review required |
|---|---|---|
| SRC-01 | CAP 1.2 describes structured emergency warning information (standard dated July 2010). | Not a validator; no UAE-specific CAP profile or conformance decision established. |
| SRC-02 | Y.3172 defines architectural concepts for ML pipeline and management/orchestration in future networks. | Does **not** certify this four-agent simulation as Y.3172-compliant; no real IMT-2020 network integration. |
| SRC-03 | UAE-Alert TS FS 001 v2.0 describes **Cell Broadcast** device warning context. | CH01 is **SMS**, so this source cannot certify CH01; verify whether a newer applicable edition exists. |
| SRC-04 | Official policy, Articles 2–3, supports accessible digital services, including emergency services in Article 2; PDF Article 1 defines senior citizens as age **60+** (different from 65+ dashboard cohort). | Whether a particular real-world operator/channel is legally in-scope, which technical checks are satisfied, and actual accessibility of deployed devices remain **Review Required**. |
| SRC-05 | Supplied law PDF supports a **textual reference** to Federal Decree-Law No. 45/2021 and its provisions; the registry remains a source locator, not a legal verdict. | Official site inaccessible in automated check (HTTP 403), and copy not authenticated as latest consolidation; legal scope/exceptions, amendments and any real deployment legal basis **Review Required**. |

## 2A. Supplementary Step 4 source (NOT a sixth Step 2 registry entry)

| Label | Title / issuer | Verified edition | Link / accessed | Scope |
|---|---|---|---|---|
| S4-AIR-2.0 | *AI Ready – Analysis Towards a Standardized Readiness Framework* / ITU-T publications | **Report 2.0, January 2026** (PDF cover; 55 PDF pages) | [Official ITU PDF](https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf), checked **2026-10-30** | Analytical AI readiness framework. Ch. 2 (printed pp. 12–16): Data, Digital Infrastructure, Digital Skills, Innovation Ecosystem and AI Policy. Ch. 3 Human Interface (printed pp. 23–24) addresses local language, usability, and special needs. **No project certification**. |

**Important:** The filename includes `2025`, but the publication cover states **January 2026**. The report disclaimer says information correct as of June 2025. These describe different things and should not be conflated. AI Readiness 2.0 is a **Step 4 supporting source**, not a retroactive edit to the frozen five-source Step 2 registry.

## 2B. Document-level check notes / unresolved verification

- **CAP 1.2:** OASIS standard HTML directly opened; title, version and **1 July 2010** verified. OASIS explicitly links a `Latest Version` location, but this review did not establish a later UAE-adopted CAP profile. No CAP pass/fail is claimed.
- **Y.3172:** ITU Recommendation page confirms **Y.3172 (06/19)**, approved **2019-06-22**, **Status: In force**. Its scope is network ML architecture, not mandated conformity for this four-agent prototype.
- **UAE-Alert:** official PDF cover confirms **TS FS 001 v2.0, 25 November 2019**. The *Scope* specifies **Cell Broadcast**, so it cannot be applied as a normative SMS CH01 specification; newer applicable edition not conclusively ruled out.
- **Digital Accessibility:** official March 2024 PDF, **20 PDF pages**, retrieved. PDF **p. 6 (Article 2)** includes mobile/telephone emergency-service accessibility; **p. 7 (Article 3)** defines applicability and differentiates federal entities from other providers; **p. 3 (Article 1)** defines senior citizens as **60+**. This supports a bounded accessibility discussion but not a finding of real-world legal compliance.
- **Data protection:** original UAE legislation URL and `/download` blocked automated access with **403**. A **user-provided local copy** titled *Federal Decree by Law No. (45) of 2021 Concerning the Protection of Personal Data* was readable, including Article 1. Do **not** claim the live original website was checked, and treat amendments / sector exceptions / applicability as unresolved.
- **AI Readiness:** ITU official PDF opened; title **Report 2.0 / January 2026** verified, analytical not certification. Broader standards mapping belongs in `maymona_standards_mapping.md` at the next stage.

**Review performed:** 2026-10-30. `Verified document` means retrievable and text examined, **not** legally current, adopted by the project, or satisfied in implementation.

## 3. Demonstrable metadata lookup (NOT document-text retrieval)

This query uses the **existing** registry and no new package. It matches source metadata; it cannot answer questions from the underlying source document text.

```bash
python -c "import json; p='lastmile_ai/knowledge/sources_registry.json'; r=json.load(open(p,encoding='utf-8')); q='accessibility'; hits=[s for s in r['sources'] if q in (' '.join(map(str,[s['title'],s['project_use'],s['agent_3_use']]))).lower()]; print([(s['id'],s['title'],s['official_url']) for s in hits])"
```

**Expected category of result:** source identifiers, titles, official URL(s), not verified extracted quotations. Metadata lookup is a **demonstration of the existing inventory**, not RAG or full Knowledge Base search. To demonstrate documentary evidence retrieval, a separate proposal should define a rights-aware source acquisition process, passage IDs, versions, anchored quotes, human checks and tests; **do not implement this without Sirin's approval**.

## 4. Core-file preservation and reproducibility

Repository files inspected (SHA-256 prefixes; for reviewer comparison, not security attestations):

| Read-only file | SHA-256 prefix |
|---|---|
| `lastmile_ai/knowledge/sources_registry.json` | `e42e740a21d2396f` |
| `lastmile_ai/knowledge/warning_fixture.json` | `957e59b8cd0a2cc8` |
| `docs/channel_actionability.md` | `45bf2e7fa3d2a20e` |
| `lastmile_ai/agents/policy_accessibility.py` | `5b1582309d26ba70` |
| `lastmile_ai/agents/evaluation.py` | `637ec9c9bf510131` |
| `lastmile_ai/schemas.py` | `42b6b72bc7e42691` |
| `lastmile_ai/runtime.py` | `448e61f3c6b08b52` |
| `lastmile_ai/pipeline.py` | `d7b26b25efcb12a4` |
| `lastmile_ai/recovery_runtime.py` | `d98907059ed22adc` |
| `lastmile_ai/data/resident_adapter.py` | `5c708674a20cb06a` |
| `lastmile_ai/metrics.py` | `67af8e83a303f8e0` |

**Open items:** confirm newer editions/amendments for UAE-Alert and PDPL; evaluate jurisdiction/application in any real deployment; decide if source-text retrieval beyond metadata is required; define passage-level citation format; no production readiness claim. **Next step:** update the separate standards-mapping document with section-level evidence, then policy gaps and claims. No source registry or agent code changed.

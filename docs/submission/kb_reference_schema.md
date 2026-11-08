# SADA AI — KB Reference Schema & Source Handoff

**Owner:** Maymona — Knowledge Base & UAE Policies  
**Date:** 8 November 2026 · **Status:** `documentation_only` · **Deliverable path:** `docs/submission/kb_reference_schema.md`

## 1. Purpose and scope

This documentation-only submission extension adds **four requested UAE official references** and the **optional UAE AI Charter** (five sources total) without editing the existing five-source runtime KB. It identifies original official URLs, issuing bodies, relevant sections, and small **editorial section-summary chunks** that can support source mapping and future ingestion design.

**Important:** `kb_reference_sources.json` is **not** ingested by the current application. Its chunk summaries are **not source quotations**, a text index, or live legal guidance. SADA's existing `lastmile_ai/knowledge/sources_registry.json`, `evidence_chunks.json`, retrieval, Qwen bridge, rules, scenario and KPIs remain unchanged. Nothing in this submission asserts legal compliance, operating authority, actual telecom/network testing, or AI security certification.

## 2. Official reference inventory

| Reference | Official issuer | Official version / page | SADA relevance | Integration |
|---|---|---|---|---|
| `UAE-REF-01` · Federal Decree by Law No. 8/2025 | UAE Federal Government | [Official text](https://uaelegislation.gov.ae/en/legislations/3231/download), **Article 4(2), 4(5), 4(6)** | Institutional role for civil defense, coordinated public warning and evacuation planning. **It establishes the Federal Authority for Ambulance and Civil Defense; it is not a law authorizing SADA.** | `documentation_only` |
| `UAE-REF-02` · National Telecom Emergency Management Plan | TRA / current TDRA | [Public strategic guide](https://tdra.gov.ae/-/media/TDRA-Media/Resources/Arabic/National-Telecom-Emergency-Management-Plan.ashx), **v1.0, 10 July 2018**; [current sector overview](https://tdra.gov.ae/en/initiatives/business-resilience-and-continuity-in-the-telecom) | Telecom-sector emergency preparedness, continuity, coordination and recovery. Public 2018 guide **not established as the latest plan**. | `documentation_only` |
| `UAE-REF-03` · UAE National AI Strategy 2031 | UAE AI Office / UAE Government | [Official strategy](https://ai.gov.ae/strategy/), **Objectives 4, 7, 8** | Responsible experimentation, usable data and governance; no product certification. | `documentation_only` |
| `UAE-REF-04` · National Cyber Security Policy for AI | UAE Cyber Security Council / UAE Government | [Official policy overview](https://u.ae/en/about-the-uae/strategies-initiatives-and-awards/policies/cyber-activities/The-National-Cyber-Security-Policy-for-Artificial-Intelligence), **Governance, Infrastructure, Algorithm Security, Operational Safety, Monitoring** | Risk, AI systems security and oversight; **full-text policy clauses not independently assessed**. | `documentation_only` |
| `UAE-REF-05` · UAE Charter for Development & Use of AI (additional) | UAE AI Office | [Official Charter PDF](https://ai.gov.ae/wp-content/uploads/2024/07/UAEAI-Methaq-EN2-3.pdf), **July 2024**, Principles 2–7, 11 | Safety, inclusion, privacy, transparency and human oversight. | `documentation_only` |

The existing runtime reference list (CAP 1.2, ITU-T Y.3172, UAE-Alert, UAE Digital Accessibility, UAE PDPL) is **not replaced or expanded here**. These new IDs are in their own namespace (`UAE-REF-*`) specifically to avoid confusing them with the existing `SRC-01`–`SRC-05` citations. The four mandatory documents are `UAE-REF-01`–`04`; the Charter is optional `UAE-REF-05`.

## 3. JSON data dictionary (portable contract)

The root JSON is an object with:

| Field | Type | Meaning |
|---|---|---|
| `project` | string | Human-readable project name; portable across sectors. |
| `artifact`, `schema_version`, `prepared_on`, `owner` | string | Provenance and handoff metadata; `prepared_on` is ISO date. |
| `integration_status` | fixed string: `documentation_only` | Explicitly states no runtime integration; **never** equate to `implemented`. |
| `source_count`, `chunk_count` | nonnegative integer | Counts of source records and chunk entries; derived/checkable. |
| `existing_runtime_registry_unchanged` | boolean | Confirms this separate documentation artifact does not edit the original runtime registry. |
| `scope_guardrails` | array of strings | Boundary statements on claims, deployment and use. |
| `sources` | array of source objects | Source identities and section summaries. |

Each `sources[]` entry:

| Field | Type / required | Description |
|---|---|---|
| `source_id` | string, unique | `UAE-REF-01` through `UAE-REF-05`; domain specific reference identifier. |
| `name`, `name_ar` | nonempty string | Official title in English and Arabic-oriented display name. |
| `issuing_authority`, `authority_role` | nonempty string | Official issuing/owning body and *bounded* institutional function; do not confuse policy issuer with simulation operator. |
| `source_type`, `published_version` | string | Document class and known edition/status (avoid inferring unknown dates). |
| `official_url` | HTTPS URL | Primary government document or page. |
| `official_reference_page` | HTTPS URL | Optional supporting government page/locator. |
| `relevant_sections` | array of strings | Human-readable precise article, objective, principle or section anchors. |
| `sada_relevance` | string | Analytical link to the SADA use case, not an implemented legal rule. |
| `integration_status` | literal `documentation_only` | Per-source status, matching root. |
| `verification` | object | `checked_on` ISO date; `basis`, `status`, and `limitations` array to declare what was/was not verified. |
| `chunks` | nonempty array | Independent section-level summaries with provenance. |

Each `chunks[]` entry:

| Field | Type / required | Description |
|---|---|---|
| `chunk_id` | unique string | Pattern `UAE-REF-XX-CYY` so the source and chunk remain linked. |
| `section` | string | Source-specific article/objective/heading; locator for reviewer. |
| `summary` | string | **Original editorial paraphrase** of the located provision/section; **not an extracted verbatim source quote**. |
| `sada_connection` | string | Explanatory project mapping; do not treat as normative content. |
| `tags` | array of strings | Optional topic labels for human navigation; no search quality claim. |
| `kind` | literal `editorial_section_summary_not_verbatim_quote` | Explicit provenance/type marker. |
| `retrieval_indexed` | boolean, **false** | Ensures we do not claim these chunks are active in a retrieval index. |

## 4. How to use the chunk format and what it does NOT establish

Example handoff path:

`UAE-REF-01 → Article 4(5) → UAE-REF-01-C02 → editorial summary → SADA institutional/operational review context`

A reviewer can open the `official_url`, go to `section`, and compare the independently written `summary` with the source. **These 15 chunks are not full source paragraphs and must not be presented as text produced by the existing retrieval engine.**

**Potential future ingestion (requires leader approval):** acquire authoritative text under its permitted terms, attach `document_version`, `source_hash`, `passage_text`, `language`, `page_or_section`, `extracted_on`, and `retrieval_indexed=true` only after actual indexing, provenance verification and evaluation. Never silently add them to the already approved SADA runtime registry.

## 5. Portability: same contract in a different domain

The shape is **domain-independent**. For example, a hypothetical *hospital evacuation planning* research project could retain the same JSON structure and use:

```json
{
  "project": "Hospital Evacuation Readiness (illustrative only)",
  "sources": [{
    "source_id": "HOSP-REF-01",
    "name": "Official hospital emergency planning guideline (example placeholder)",
    "issuing_authority": "[verified issuer required]",
    "official_url": "https://example.org/replace-with-verified-official-link",
    "integration_status": "documentation_only",
    "chunks": [{
      "chunk_id": "HOSP-REF-01-C01",
      "section": "[verified section required]",
      "summary": "[editorial paraphrase pending source check]",
      "kind": "editorial_section_summary_not_verbatim_quote",
      "retrieval_indexed": false
    }]
  }]
}
```

This **illustrates the reusable fields**; the placeholder is not an approved source. To use the format in another sector, replace titles, issuers, URLs, section anchors and summaries with verified official references, and adopt a new source namespace. **Keep source provenance and cautious integration status.**

## 6. QA / handoff checks

- Exactly **5 sources**: 4 required + 1 optional UAE AI Charter.
- Exactly **15 section-summary chunks**, three per source; all IDs unique and trace to a source.
- Every source has the official issuer, official HTTPS URL, documented relevant sections, SADA relevance, verification caveats and `integration_status: documentation_only`.
- No source entry is represented as automatically retrieved evidence; `retrieval_indexed: false` for every chunk.
- The older **2018 TDRA plan** is described as a **published edition**, not necessarily latest.
- No changes to existing Agents, website, source registry, lexical/vector retrieval, Qwen integration, datasets, or KPIs.
- This submission is **policy/standards research evidence**, not legal interpretation, live deployment authorization, or cybersecurity certification.

## 7. Quick validation commands

Run from any folder containing the JSON file:

```bash
python -m json.tool kb_reference_sources.json
python -c "import json; d=json.load(open('kb_reference_sources.json',encoding='utf-8')); s=d['sources']; assert len(s)==d['source_count']==5; assert sum(len(x['chunks']) for x in s)==d['chunk_count']==15; assert all(x['integration_status']=='documentation_only' and all(c['retrieval_indexed'] is False for c in x['chunks']) for x in s); print('Maymona KB reference validation PASSED')"
```

**Submission location:** `docs/submission/kb_reference_sources.json`, `docs/submission/kb_reference_schema.md`. Add only these two files via an independent PR/commit after the team leader's review.

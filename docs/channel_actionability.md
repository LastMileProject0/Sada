# LastMile AI — Channel Actionability Matrix (Sirin-approved Step 2 update)

**Owner:** Maymona · **Baseline:** Approved Step 1 Master (23 October 2026) · **Approval:** Sirin’s explicit Arabic warning and channel-rendering decisions · **Status:** Content approved; integration/TTS media and runtime tests pending.

## 1. Fixed Arabic warning

**Canonical warning (approved verbatim):**

تدريب فقط — تحذير من سيول مفاجئة في منطقة الوادي.

تسببت الأمطار الغزيرة في خطر افتراضي لحدوث سيول مفاجئة في منطقة الوادي. ابتعدوا عن مياه السيول والمناطق المنخفضة، وانتقلوا إلى أماكن مرتفعة إذا كان ذلك آمناً. اتبعوا تعليمات جهة الطوارئ الافتراضية.

The Al Wadi area, issuing authority, residents, and emergency are fictional. **EXERCISE ONLY:** no real alert is issued. Content is fixed across T+00:00/T+02:00/T+04:00/T+06:00 and P0–P3. The channel-specific variants below are pre-approved and fixed, not dynamically generated or tailored by AI. `warning_fixture.json` is the machine-readable source of exact approved renderings.

## 2. Approved channel representations

### CH01 — SMS

**Approved Arabic SMS text (verbatim):**

> تدريب فقط: خطر سيول في منطقة الوادي. ابتعد عن مياه السيول والمناطق المنخفضة، وانتقل إلى مكان مرتفع إذا كان آمناً.

- Arabic direction: RTL; Arabic SMS is assumed to require Unicode-compatible encoding (UCS-2/UTF-16 family). The text contains **113 UTF-16 code units**. Under an illustrative 70-unit single segment / 67-unit multipart segment model, this is **2 segments**. Actual provider/device behavior is not verified; log this as a modeling assumption, **not** an observed delivery fact.
- `SMS failed EV01` / network status remains Agent 1's technical concern. SMS is **not** UAE-Alert Cell Broadcast.
- Do **not** assume receipt of all parts. Missing/truncated/uncertain received content → `Needs Further Review` for content sufficiency; do not count as confirmed effective coverage.
- Text usability for each resident must be explicitly established; disability categories alone do not settle it.

### CH02 — Mobile App

**Approved full alert screen (Arabic, RTL):**

- **Headline:** تحذير من سيول مفاجئة — منطقة الوادي (تدريب فقط)
- **Description:** تسببت الأمطار الغزيرة في خطر افتراضي لحدوث سيول مفاجئة.
- **Protective Instructions:** ابتعد عن مياه السيول والمناطق المنخفضة. انتقل إلى مكان مرتفع إذا كان ذلك آمناً. اتبع تعليمات جهة الطوارئ الافتراضية.

Instructions are assumed visible in the **full warning screen**, not merely in a short push notification. `Emergency app installed=Yes` is a preliminary eligibility prerequisite for the 600 residents with the installed flag; installation never proves delivery or accessibility. Do not assume screen readers, vibration, translation or other access features unless explicitly recorded in the model. Resident-specific display usability may still require review.

### CH03 — Voice Call (Arabic TTS)

**Approved spoken script (verbatim):**

هذا تدريب فقط.

تحذير من سيول مفاجئة في منطقة الوادي نتيجة الأمطار الغزيرة.

يرجى الابتعاد عن مياه السيول والمناطق المنخفضة.

انتقلوا إلى أماكن مرتفعة إذا كان ذلك آمناً، واتبعوا تعليمات جهة الطوارئ الافتراضية.

نؤكد أن هذا تدريب فقط.

- An **Arabic Text-to-Speech** audio recording will be produced for **simulation/demo use only**; producing an MP3/WAV and integrating it is **not Maymona’s deliverable** at this stage.
- `tts_audio_file` and `audio_duration_seconds` remain `null` until real media exists and is measured. **Simulated call arrival time and playback duration are separate metrics.** Call arrival does not prove all instructions were played/heard or understood.
- Use the resident's `Voice usable` flag for known barriers (`No` with a delivered warning → `Accessibility Barrier`); unknown audio completion or suitability → review rather than automatic success.

### CH04 — Public Sirens

**Alert-only, nonverbal acoustic signal.** No spoken content, TTS, or protective instructions. A selected technical arrival may count for **Estimated Reach**, but sirens **never alone** qualify for Effective Warning Coverage, even at <=30 s. Audibility and specific resident usability are evaluated separately.

### CH05 — Digital Signage

**Approved Arabic display text (verbatim):**

تدريب فقط — خطر سيول

منطقة الوادي

ابتعد عن مياه السيول والمناطق المنخفضة.

اتجه إلى مكان مرتفع إذا كان آمناً.

Assume the screen is capable of showing the **entire** approved Arabic text in a clear font. This is a synthetic display assumption, not evidence that every resident sees/reads it. Use `In signage area` for preliminary eligibility and `Signage readable` for person-level presentation usability; `No` with arrival → `Accessibility Barrier`. Incomplete/unknown content or viewing circumstances → review.

## 3. Reproducible Content Sufficiency (separate from delivery/accessibility)

The actual modeled **received/rendered** channel content must be checked for all three:

1. **Hazard Present** — clear flood hazard.
2. **Affected Area Present** — Al Wadi.
3. **Protective Instruction Present** — clear instructions to avoid floodwaters/low ground and/or move to safer higher ground.

- `Sufficient`: all three are evidenced in the actual modeled received rendering.
- `Insufficient`: at least one required item is confirmed absent.
- `Needs Further Review`: the content/receipt/evidence is incomplete or uncertain. **Never auto-pass**.

Approved full screen/script/text does **not** prove actual receipt of every part or individual usability. CH04 sirens remain alert-only (insufficient standalone instructions).

## 4. Effective Warning Coverage gate

To count one resident in simulated Effective Warning Coverage, require **all**: actually selected channel in the tested plan; arrival within **<=30 simulated seconds**; content `Sufficient` with actionable instruction; individually supported format usability. `Delayed` (>30 and <=60 s) contributes to Estimated Reach only. `Failed`, `Unavailable`, no eligible channel, unsupported usability, incomplete content or unknown evidence cannot be counted as confirmed effective. Use unique residents, not sum of attempts.

Agent 1 determines technical status (`Delivered`, `Delayed`, `Failed`, `Unavailable`). `No Eligible Channel` belongs to plan assignment. Agent 2 technical priority uses actual selected results only. Agent 3 accessibility values include `Usable in Simulation`, `Accessibility Barrier`, `Needs Further Review`, **`Not Assessed—No Delivery`** (exact Salma schema spelling). Authorization and Privacy remain separate: `No Issue Identified`, `Review Required`, `Insufficient Information`, `Not Applicable`. They do not constitute legal clearance.

## 5. Evidence handoff / integration mapping (suggested, not schema amendment)

For the actual selected attempt, preserve `warning_id`, `resident_id`, `channel_id`, `plan_id`, `stage`, actual rendered content reference, hazard/area/instruction checks, receipt/completeness evidence, individual usability, `content_sufficiency`, reason and source basis. These are **proposed evidence concepts**, not mandatory keys added to Salma’s `schemas.py`.

Salma’s Agent 3 linkage fields are `warning_fixture_id`, `actionability_rules_id`, `source_registry_id` and its finding includes `actionable`, `reason`, `evidence`. Determine reference IDs, storage and loader integration with Salma/Sirin; the files alone do not implement an agent. The authoritative registry IDs are `SRC-01`…`SRC-05` (CAP: `SRC-01`, not legacy `CAP_1_2`). Dataset Yes/No -> Python boolean conversion is handled in dataset/integration layer without editing Ethar’s spreadsheet.

## 6. Reference restrictions and pending execution tasks

Five sources only: CAP 1.2 advisory knowledge, ITU-T Y.3172 architectural inspiration, UAE-Alert Cell Broadcast device context (not SMS), UAE Digital Accessibility Policy, UAE Personal Data Protection Law. No CAP XML validator, legal certification, CH06, real telecom integration or invented KPI outcomes. EV03 hypothetical external channel is excluded from permitted backups.

**Approved now:** Arabic canonical warning, four channel text/script renderings, nonverbal sirens, Arabic TTS choice and fixed content-sufficiency test.

**Still pending execution:** MP3/WAV and recording length, SMS segmentation/complete receipt simulation, person-specific uncertain accessibility assumptions, mapping to Salma contracts and end-to-end tests. These are not further approvals of the wording.

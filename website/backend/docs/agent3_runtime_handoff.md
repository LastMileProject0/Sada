# Agent 3 — Step 3 Runtime Handoff (Maymona)

## Files
- `lastmile_ai/agents/policy_accessibility.py`: evaluates arrived *selected* resident/channel attempts against fixed Arabic warning, recorded usability flags, and scenario-based authorization/privacy; returns Salma's `Agent3Output` dataclasses.
- `lastmile_ai/agents/evaluation.py`: deterministic, channel-specific content-sufficiency check (Hazard / Area / Protective Instruction); separate from delivery and individual usability.
- `tests/test_agent3_runtime.py`: focused tests.

## Invocation
```python
from lastmile_ai.agents.policy_accessibility import assess_agent3
result = assess_agent3(agent3_input)  # Agent3Input from schemas.py
result.validate_against_input(agent3_input)
```
Use exactly these `Agent3Input` fixture identifiers:
- `warning_fixture_id='ALWADI-FLOOD-EXERCISE-001'`
- `actionability_rules_id='channel_actionability.md'`
- `source_registry_id='sources_registry'`

Fixtures are loaded read-only from `lastmile_ai/knowledge/`. No files or contracts are mutated.

## Important evidence boundary
The optional `rendering_evidence` argument is a mapping of `(resident_id, channel_id)` to flags:
`complete_rendering_received` (SMS multipart completeness, app/signage rendering evidence),
`audio_playback_completed` (separate from voice-call arrival), and `format_usable`
(explicit individual text/app usability evidence). Missing flags are **not** positive evidence.

App and signage display-content assumptions come from the approved static fixture; individual app/text accessibility is never inferred automatically. SMS cannot pass with unknown multipart completeness; voice TTS cannot pass with unknown playback completion; a siren never passes standalone actionability. A known `Voice usable=No` or `Signage readable=No` becomes `Accessibility Barrier` after arrival. `Not Assessed—No Delivery` applies when no selected arrival occurred.

**Important:** `actionable=True` means only that the fixed content check and individual format check have evidence; it does **not** mean Effective Warning Coverage. The eventual KPI/pipeline must ALSO require an actual selected delivery <=30 seconds. Delayed deliveries may still be content-actionable, but must not count toward Effective Warning Coverage.

## Policy limitations
At T+06:00 both policy findings indicate `Review Required` on the *hypothetical EV03 outside channel only*. EV03 is not used for delivery or fallback and this finding must **not** block internal CH01–CH05. At earlier stages, `No Issue Identified` means only under documented synthetic scenario, not lawful/compliant certification. CAP advisory is cited as `SRC-01`; never CAP pass/fail.

## Integration work for Sirin / teammates
1. Pass approved fixture identifiers via `Agent3Input`.
2. Attach channel-rendering/receipt and usability evidence as available. Agent 1's `Delivered` outcome alone does not establish full multipart SMS receipt or complete TTS listening.
3. In KPI computation, combine Agent 1 arrival time, Agent 3 usability status and `actionable=True`. Do not count `Needs Further Review` as confirmed success.
4. Re-run Agent 3 for each tested recovery plan with the **same** stage, resident profile, and fixed warning.
5. Real TTS audio and its separate duration remain a later integration item; no audio created here.

## Known MVP limits
There is no automatic CAP XML validator, real alert sending, TTS synthesis, or legal determination. The lexical fixed-Arabic content check is a transparent simulation proxy, not a natural-language understanding or actual resident comprehension test. Authorization/Privacy cases are scenario-based and not an exhaustive review of UAE law.

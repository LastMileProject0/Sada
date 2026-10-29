"""Deterministic channel-content checks for the approved Arabic warning fixture.

Content sufficiency is independent of resident usability and network delivery.
Unknown evidence must not be turned into a success. No free-form text generation.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Any
from lastmile_ai.schemas import ChannelID

class ContentStatus(str, Enum):
    SUFFICIENT = 'Sufficient'
    INSUFFICIENT = 'Insufficient'
    REVIEW = 'Needs Further Review'

@dataclass(frozen=True)
class ContentAssessment:
    status: ContentStatus
    hazard_present: bool | None
    area_present: bool | None
    protective_instruction_present: bool | None
    reason: str


def evaluate_content(channel: ChannelID, fixture: Mapping[str, Any],
                     *, complete_rendering_received: bool | None = None,
                     audio_playback_completed: bool | None = None) -> ContentAssessment:
    """Evaluate approved fixed renderings; optional runtime evidence may confirm receipt/playback.

    `complete_rendering_received` MUST come from simulation evidence, not simply
    from a successful delivery record. For the app/signage, Step 2 fixture explicitly
    assumes complete text display; this is still not proof of individual usability.
    """
    renders = fixture['approved_channel_renderings']
    info = renders[channel.value]
    if channel is ChannelID.PUBLIC_SIRENS:
        return ContentAssessment(ContentStatus.INSUFFICIENT, True, None, False,
                                 'CH04 is nonverbal alert-only; no protective instructions.')
    if channel is ChannelID.SMS:
        if complete_rendering_received is not True:
            return ContentAssessment(ContentStatus.REVIEW, None, None, None,
                                     'Arabic multipart SMS: complete receipt of all segments is not evidenced.')
        content = info['text']
    elif channel is ChannelID.VOICE_CALL:
        if audio_playback_completed is not True:
            return ContentAssessment(ContentStatus.REVIEW, None, None, None,
                                     'Call arrival does not establish complete Arabic TTS playback.')
        content = info['spoken_script']
    elif channel is ChannelID.MOBILE_APP:
        if complete_rendering_received is False:
            return ContentAssessment(ContentStatus.INSUFFICIENT, None, None, False,
                                     'App full alert screen is confirmed incomplete.')
        if complete_rendering_received is None and info.get('full_instructions_visible_assumption') is not True:
            return ContentAssessment(ContentStatus.REVIEW, None, None, None, 'App screen completeness unknown.')
        content = ' '.join(info['content'].values())
    elif channel is ChannelID.DIGITAL_SIGNAGE:
        if complete_rendering_received is False:
            return ContentAssessment(ContentStatus.INSUFFICIENT, None, None, False,
                                     'Digital sign is confirmed incomplete.')
        if complete_rendering_received is None and not info.get('simulation_display_assumption'):
            return ContentAssessment(ContentStatus.REVIEW, None, None, None, 'Sign rendering unknown.')
        content = info['display_text']
    else:
        raise ValueError(f'Unknown channel: {channel}')
    # Fixed, approved Arabic renderings. This is a documented content-proxy check,
    # not semantic AI interpretation or real-world comprehension verification.
    hazard = 'سيول' in content
    area = 'الوادي' in content
    protective = ('ابتعد' in content or 'الابتعاد' in content) and ('مرتفع' in content or 'مرتفعة' in content)
    status = ContentStatus.SUFFICIENT if all((hazard, area, protective)) else ContentStatus.INSUFFICIENT
    return ContentAssessment(status, hazard, area, protective,
                             'Fixed Arabic rendering checked for hazard, area and protective actions; no comprehension claim.')

"""Evidence-aware, stage-specific accessibility barrier assessment.

Ethar's isolated handoff for EV02. This module does not alter the Master
Dataset, delivery simulation, Agent 3, Agent 4, or plan selection.

A pre-EV02 UNKNOWN is *not* evidence that the channel is usable.
A recorded Yes means no barrier is recorded for that specific channel
attribute, not verified accessibility or effective warning coverage.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from lastmile_ai.schemas import ChannelID, EventStage, ResidentProfile


class BarrierStatus(str, Enum):
    ACTIVE_EV02 = "Active EV02"
    ACTIVE_PERMANENT = "Active Permanent"
    UNKNOWN = "Unknown"
    NO_RECORDED_BARRIER = "No Recorded Barrier"
    NOT_ASSESSED = "Not Assessed"


@dataclass(frozen=True)
class BarrierAssessment:
    resident_id: str
    channel_id: ChannelID
    stage: EventStage
    status: BarrierStatus
    evidence: str

    @property
    def confirmed_barrier(self) -> bool:
        return self.status in (
            BarrierStatus.ACTIVE_EV02,
            BarrierStatus.ACTIVE_PERMANENT,
        )

    @property
    def confirmed_usable(self) -> bool:
        """This module never establishes complete end-to-end usability."""
        return False


def assess_accessibility_barrier(
    resident: ResidentProfile,
    channel: ChannelID,
    stage: EventStage,
) -> BarrierAssessment:
    """Assess documented Voice/Signage barriers without guessing onset.

    Zone B recorded No flags in the documented EV02 groups are considered
    linked to EV02, active at T+04/T+06 and UNKNOWN at T+00/T+02.
    Other recorded No flags lack sufficient onset evidence in the supplied
    Profile Rules/Change Log and remain UNKNOWN across stages.

    No resident is asserted to have a permanent barrier merely because a
    static dataset flag is No; permanent evidence requires an independent
    provenance source. `ACTIVE_PERMANENT` is reserved for such evidence
    once approved, and is not currently emitted by this function.
    """
    if not isinstance(resident, ResidentProfile):
        raise TypeError("resident must be ResidentProfile")
    if not isinstance(channel, ChannelID):
        raise TypeError("channel must be ChannelID")
    if not isinstance(stage, EventStage):
        raise TypeError("stage must be EventStage")

    if channel == ChannelID.VOICE_CALL:
        flagged = resident.hearing_impairment and not resident.voice_usable
        flag_name = "Voice usable=No with hearing impairment"
        yes_value = resident.voice_usable
        applicable = True
    elif channel == ChannelID.DIGITAL_SIGNAGE:
        flagged = resident.visual_impairment and not resident.signage_readable
        flag_name = "Signage readable=No with visual impairment"
        yes_value = resident.signage_readable
        applicable = True
    else:
        flagged = False
        yes_value = False
        applicable = False
        flag_name = ""

    if not applicable:
        return BarrierAssessment(
            resident.resident_id, channel, stage,
            BarrierStatus.NOT_ASSESSED,
            "EV02 evidence concerns Voice Call and Digital Signage only; "
            "this channel is not assessed here.",
        )

    if flagged and resident.zone == "Zone B":
        if stage in (EventStage.T04, EventStage.T06):
            return BarrierAssessment(
                resident.resident_id, channel, stage,
                BarrierStatus.ACTIVE_EV02,
                f"BL-01 / EV02: Zone B; {flag_name}; active from T+04. "
                "No assertion about the barrier's first real-world onset.",
            )
        return BarrierAssessment(
            resident.resident_id, channel, stage,
            BarrierStatus.UNKNOWN,
            f"BL-01 / EV02: Zone B; {flag_name}; the earlier-stage "
            "barrier state is unproven. Unknown does not mean usable.",
        )

    if not yes_value:
        return BarrierAssessment(
            resident.resident_id, channel, stage,
            BarrierStatus.UNKNOWN,
            f"Static resident profile records {flag_name if flagged else 'channel usability=No'}; "
            "the Profile Rules and Change Log do not establish permanent "
            "versus event-linked origin for this resident. Do not assume usable.",
        )

    return BarrierAssessment(
        resident.resident_id, channel, stage,
        BarrierStatus.NO_RECORDED_BARRIER,
        "Resident-level channel flag=Yes in the approved synthetic profile; "
        "no barrier is recorded for this channel attribute. This is not "
        "proof of delivery, full accessibility, comprehension, or coverage.",
    )

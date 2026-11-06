
from lastmile_ai.schemas import EventStage, ResidentProfile


def is_sms_outage_active(
    resident: ResidentProfile,
    stage: EventStage
) -> bool:
    """
    Check whether EV01 SMS outage affects
    a resident at the selected scenario stage.
    """

    # No SMS outage at baseline
    if stage == EventStage.T00:
        return False

    # EV01 remains active at T+02, T+04 and T+06
    if stage in (
        EventStage.T02,
        EventStage.T04,
        EventStage.T06
    ):
        return (
            resident.zone == "Zone B"
            and resident.sms_failed_ev01
        )

    raise ValueError("Invalid event stage")


def is_ev02_active(stage: EventStage) -> bool:
    """
    Check whether EV02 accessibility conditions
    are active in the cumulative scenario.
    """

    if not isinstance(stage, EventStage):
        raise ValueError("Invalid event stage")

    return stage in (
        EventStage.T04,
        EventStage.T06
    )


def is_ev03_active(stage: EventStage) -> bool:
    """
    Check whether EV03 policy-review conditions
    are active in the cumulative scenario.
    """

    if not isinstance(stage, EventStage):
        raise ValueError("Invalid event stage")

    return stage == EventStage.T06


def is_channel_eligible(
    resident: ResidentProfile,
    channel
) -> bool:
    """
    Check resident-specific hard prerequisites.

    The channel must also be enabled in the
    simulation configuration.
    """

    from lastmile_ai.schemas import ChannelID

    if not isinstance(channel, ChannelID):
        raise TypeError("channel must be ChannelID")

    if channel == ChannelID.MOBILE_APP:
        return resident.emergency_app_installed

    if channel == ChannelID.PUBLIC_SIRENS:
        return resident.in_siren_area

    if channel == ChannelID.DIGITAL_SIGNAGE:
        return resident.in_signage_area

    if channel in (ChannelID.SMS, ChannelID.VOICE_CALL):
        return True

    raise ValueError("Unsupported channel")

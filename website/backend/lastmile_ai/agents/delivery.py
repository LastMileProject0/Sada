
import hashlib

TIMING_MODEL_VERSION = "lastmile-timing-v1"


def stable_hash_value(
    resident_id: str,
    channel_id: str,
    calculation_type: str
) -> float:
    """
    Generate a reproducible value in [0, 1).

    The hash does not depend on plan_id
    or selected_stage.
    """

    if calculation_type not in ("failure", "delay"):
        raise ValueError("Invalid calculation type")

    key = (
        f"{TIMING_MODEL_VERSION}|"
        f"{resident_id}|"
        f"{channel_id}|"
        f"{calculation_type}"
    )

    digest = hashlib.sha256(
        key.encode("utf-8")
    ).digest()

    # Convert first 8 bytes to a 64-bit unsigned integer
    number = int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False
    )

    return number / (2 ** 64)


from lastmile_ai.schemas import ChannelID


CHANNEL_TIMING_RULES = {
    ChannelID.SMS: {
        "min_delay": 8,
        "max_delay": 25,
        "failure_probability": 0.05
    },
    ChannelID.MOBILE_APP: {
        "min_delay": 5,
        "max_delay": 20,
        "failure_probability": 0.08
    },
    ChannelID.VOICE_CALL: {
        "min_delay": 10,
        "max_delay": 30,
        "failure_probability": 0.07
    },
    ChannelID.PUBLIC_SIRENS: {
        "min_delay": 3,
        "max_delay": 12,
        "failure_probability": 0.03
    },
    ChannelID.DIGITAL_SIGNAGE: {
        "min_delay": 5,
        "max_delay": 15,
        "failure_probability": 0.05
    }
}


def is_base_failure(resident_id: str, channel_id: ChannelID) -> bool:
    """
    Determine deterministic base failure using SHA-256.

    This excludes scenario-specific failures such as EV01.
    """

    if not isinstance(channel_id, ChannelID):
        raise TypeError("channel_id must be ChannelID")

    failure_value = stable_hash_value(
        resident_id,
        channel_id.value,
        "failure"
    )

    failure_probability = CHANNEL_TIMING_RULES[
        channel_id
    ]["failure_probability"]

    return failure_value < failure_probability


def calculate_base_delay(
    resident_id: str,
    channel_id: ChannelID
) -> int:
    """
    Calculate deterministic base delay in whole seconds.

    Both the minimum and maximum delays are inclusive.
    """

    if not isinstance(channel_id, ChannelID):
        raise TypeError("channel_id must be ChannelID")

    rules = CHANNEL_TIMING_RULES[channel_id]

    min_delay = rules["min_delay"]
    max_delay = rules["max_delay"]

    delay_value = stable_hash_value(
        resident_id,
        channel_id.value,
        "delay"
    )

    # Map [0, 1) to an inclusive integer range
    base_delay = min_delay + int(
        delay_value * (max_delay - min_delay + 1)
    )

    return base_delay


def calculate_network_penalty(
    resident,
    channel_id: ChannelID
) -> int:
    """
    Calculate approved network delay penalties.

    Weak mobile coverage:
        +15 seconds for SMS and Voice Call.

    Limited internet:
        +20 seconds for Mobile App.
    """

    if not isinstance(channel_id, ChannelID):
        raise TypeError("channel_id must be ChannelID")

    if channel_id in (
        ChannelID.SMS,
        ChannelID.VOICE_CALL
    ):
        return 15 if resident.weak_mobile_coverage else 0

    if channel_id == ChannelID.MOBILE_APP:
        return 20 if resident.limited_internet else 0

    return 0


from lastmile_ai.schemas import DeliveryStatus, EventStage
from lastmile_ai.agents.scenario_conditions import (
    is_channel_eligible,
    is_sms_outage_active
)


def classify_arrival_time(arrival_seconds: int) -> DeliveryStatus:
    """
    Classify a simulated arrival using approved time boundaries.
    """
    if arrival_seconds < 0:
        raise ValueError("Arrival time cannot be negative")

    if arrival_seconds <= 30:
        return DeliveryStatus.DELIVERED

    if arrival_seconds <= 60:
        return DeliveryStatus.DELAYED

    return DeliveryStatus.FAILED


def calculate_delivery_outcome(
    resident,
    channel_id: ChannelID,
    selected_stage: EventStage
) -> dict:
    """
    Calculate deterministic technical delivery outcome.

    This function does not perform accessibility assessment.
    """

    if not isinstance(channel_id, ChannelID):
        raise TypeError("channel_id must be ChannelID")

    if not isinstance(selected_stage, EventStage):
        raise TypeError("selected_stage must be EventStage")

    # 1. Check hard prerequisites
    if not is_channel_eligible(resident, channel_id):
        return {
            "status": DeliveryStatus.UNAVAILABLE,
            "attempted": False,
            "arrival_time_seconds": None,
            "reason": "Hard prerequisite not satisfied",
            "evidence": {
                "channel_id": channel_id.value
            }
        }

    # 2. Apply deterministic EV01 outage
    if (
        channel_id == ChannelID.SMS
        and is_sms_outage_active(resident, selected_stage)
    ):
        return {
            "status": DeliveryStatus.FAILED,
            "attempted": True,
            "arrival_time_seconds": None,
            "reason": "EV01 SMS outage",
            "evidence": {
                "event": "EV01",
                "stage": selected_stage.value,
                "zone": resident.zone
            }
        }

    # 3. Apply base failure
    if is_base_failure(resident.resident_id, channel_id):

        failure_hash = stable_hash_value(
            resident.resident_id,
            channel_id.value,
            "failure"
        )

        failure_probability = CHANNEL_TIMING_RULES[
            channel_id
        ]["failure_probability"]

        return {
            "status": DeliveryStatus.FAILED,
            "attempted": True,
            "arrival_time_seconds": None,
            "reason": "Deterministic base failure",
            "evidence": {
                "model_version": TIMING_MODEL_VERSION,
                "channel_id": channel_id.value,
                "failure_hash_value": failure_hash,
                "failure_probability": failure_probability,
                "failure_rule": "hash < probability"
            }
        }

    # 4. Calculate arrival delay
    base_delay = calculate_base_delay(
        resident.resident_id,
        channel_id
    )

    network_penalty = calculate_network_penalty(
        resident,
        channel_id
    )

    total_delay = base_delay + network_penalty

    # 5. Classify the outcome
    status = classify_arrival_time(total_delay)

    if status == DeliveryStatus.FAILED:
        return {
            "status": status,
            "attempted": True,
            "arrival_time_seconds": None,
            "reason": "Delivery exceeded 60-second window",
            "evidence": {
                "base_delay_seconds": base_delay,
                "network_penalty_seconds": network_penalty,
                "calculated_delay_seconds": total_delay
            }
        }

    return {
        "status": status,
        "attempted": True,
        "arrival_time_seconds": total_delay,
        "reason": "Deterministic delivery simulation",
        "evidence": {
            "model_version": TIMING_MODEL_VERSION,
            "base_delay_seconds": base_delay,
            "network_penalty_seconds": network_penalty,
            "calculated_delay_seconds": total_delay
        }
    }


import json
from lastmile_ai.schemas import DeliveryRecord


def create_selected_delivery_record(
    resident,
    channel_id: ChannelID,
    selected_stage: EventStage,
    plan_id: str
) -> DeliveryRecord:
    """
    Create a DeliveryRecord for a selected channel.

    Uses the approved deterministic simulation.
    """

    outcome = calculate_delivery_outcome(
        resident,
        channel_id,
        selected_stage
    )

    return DeliveryRecord(
        resident_id=resident.resident_id,
        plan_id=plan_id,
        channel_id=channel_id,
        status=outcome["status"],
        selected_in_plan=True,
        attempted=outcome["attempted"],
        attempt_time_seconds=(
            0 if outcome["attempted"] else None
        ),
        arrival_time_seconds=outcome["arrival_time_seconds"],
        reason=outcome["reason"],
        evidence=json.dumps(
            outcome["evidence"],
            ensure_ascii=False,
            sort_keys=True
        )
    )


def create_potential_delivery_record(
    resident,
    channel_id: ChannelID,
    selected_stage: EventStage,
    plan_id: str
) -> DeliveryRecord:
    """
    Evaluate a potential channel without an actual attempt.

    Potential evaluations must not contribute to actual reach.
    """

    # Calculate counterfactual technical outcome
    outcome = calculate_delivery_outcome(
        resident,
        channel_id,
        selected_stage
    )

    evidence = {
        **outcome["evidence"],
        "evaluation_type": "potential",
        "actual_attempt": False
    }

    return DeliveryRecord(
        resident_id=resident.resident_id,
        plan_id=plan_id,
        channel_id=channel_id,
        status=outcome["status"],
        selected_in_plan=False,
        attempted=False,
        attempt_time_seconds=None,
        arrival_time_seconds=outcome["arrival_time_seconds"],
        reason="Potential evaluation: " + outcome["reason"],
        evidence=json.dumps(
            evidence,
            ensure_ascii=False,
            sort_keys=True
        )
    )


from lastmile_ai.schemas import (
    Agent1Input,
    Agent1Output,
    AssignmentStatus,
)


def run_agent1(agent_input: Agent1Input) -> Agent1Output:
    """
    Run Agent 1 using the supplied plan assignments.

    Selected records represent actual simulated selections.
    Potential records are counterfactual evaluations only.
    """

    if not isinstance(agent_input, Agent1Input):
        raise TypeError("agent_input must be Agent1Input")

    selected_records = []
    potential_records = []
    no_eligible_assignments = []

    stage = agent_input.configuration.selected_stage
    enabled_channels = agent_input.configuration.enabled_channels
    plan_id = agent_input.plan_id

    residents_by_id = {
        resident.resident_id: resident
        for resident in agent_input.residents
    }

    for assignment in agent_input.assignments:

        resident = residents_by_id[assignment.resident_id]

        # No Eligible Channel: no selected delivery record
        if assignment.assignment_status == AssignmentStatus.NO_ELIGIBLE_CHANNEL:
            no_eligible_assignments.append(assignment)

            # Evaluate enabled channels as potential only
            for channel in enabled_channels:
                potential_records.append(
                    create_potential_delivery_record(
                        resident, channel, stage, plan_id
                    )
                )

            continue

        selected_channel = assignment.selected_channel

        # Selected channel
        selected_records.append(
            create_selected_delivery_record(
                resident,
                selected_channel,
                stage,
                plan_id
            )
        )

        # Other enabled channels are potential
        for channel in enabled_channels:

            if channel == selected_channel:
                continue

            potential_records.append(
                create_potential_delivery_record(
                    resident,
                    channel,
                    stage,
                    plan_id
                )
            )

    output = Agent1Output(
        plan_id=plan_id,
        selected_delivery_records=tuple(selected_records),
        potential_channel_evaluations=tuple(potential_records),
        no_eligible_assignments=tuple(no_eligible_assignments)
    )

    output.validate_against_input(agent_input)

    return output

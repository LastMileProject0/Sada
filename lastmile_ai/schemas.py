"""LastMile AI — Step 2.1: planner-controlled Simulation Configuration.

Source: approved Step 1 Master (23 Oct 2026), FR-01.
Only the event stage and enabled five-channel set are planner-editable.
This module does NOT load/edit the fixed 1,000-resident dataset or execute simulation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class EventStage(str, Enum):
    T00 = "T+00:00"
    T02 = "T+02:00"
    T04 = "T+04:00"
    T06 = "T+06:00"


class ChannelID(str, Enum):
    SMS = "CH01"
    MOBILE_APP = "CH02"
    VOICE_CALL = "CH03"
    PUBLIC_SIRENS = "CH04"
    DIGITAL_SIGNAGE = "CH05"


# Read-only scenario constants (not user inputs).
SCENARIO_ID = "AL_WADI_FLASH_FLOOD"
RESIDENT_COUNT = 1000
OBSERVATION_WINDOW_SECONDS = 60
ON_TIME_DEADLINE_SECONDS = 30
CHANNEL_PRIORITY_P0 = (
    ChannelID.SMS,
    ChannelID.VOICE_CALL,
    ChannelID.MOBILE_APP,
    ChannelID.PUBLIC_SIRENS,
    ChannelID.DIGITAL_SIGNAGE,
)


@dataclass(frozen=True)
class SimulationConfiguration:
    """Valid planner inputs for one cumulative snapshot simulation.

    Input contains exactly two editable fields: selected_stage, enabled_channels.
    The engine provides scenario data and P0 assignment separately.
    """

    selected_stage: EventStage
    enabled_channels: tuple[ChannelID, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.selected_stage, EventStage):
            raise ValueError("selected_stage must be one of T+00:00, T+02:00, T+04:00, T+06:00")
        if not isinstance(self.enabled_channels, tuple):
            raise TypeError("enabled_channels must be a tuple of ChannelID values")
        if not self.enabled_channels:
            raise ValueError("At least one channel must be enabled")
        if any(not isinstance(ch, ChannelID) for ch in self.enabled_channels):
            raise ValueError("Each enabled channel must be a valid CH01–CH05 ChannelID")
        if len(set(self.enabled_channels)) != len(self.enabled_channels):
            raise ValueError("Duplicate enabled channels are not permitted")
        # Stable order by channel ID; P0 priority is a separate constant above.
        object.__setattr__(self, "enabled_channels", tuple(sorted(self.enabled_channels, key=lambda x: x.value)))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SimulationConfiguration":
        if not isinstance(data, Mapping):
            raise TypeError("Simulation Configuration must be an object")
        required = {"selected_stage", "enabled_channels"}
        extra = set(data) - required
        missing = required - set(data)
        if missing or extra:
            raise ValueError(f"Configuration keys mismatch: missing={sorted(missing)}, extra={sorted(extra)}")
        try:
            stage = EventStage(data["selected_stage"])
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid selected_stage") from exc
        raw_channels = data["enabled_channels"]
        if not isinstance(raw_channels, list):
            raise TypeError("enabled_channels must be a JSON array")
        try:
            channels = tuple(ChannelID(value) for value in raw_channels)
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid channel; allowed values are CH01–CH05") from exc
        return cls(selected_stage=stage, enabled_channels=channels)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_stage": self.selected_stage.value,
            "enabled_channels": [channel.value for channel in self.enabled_channels],
        }


# Step 2.2 — Agent 1 interfaces. No simulation is executed here.
class DeliveryStatus(str, Enum):
    DELIVERED = "Delivered"
    DELAYED = "Delayed"
    FAILED = "Failed"
    UNAVAILABLE = "Unavailable"


class AssignmentStatus(str, Enum):
    ASSIGNED = "Assigned"
    NO_ELIGIBLE_CHANNEL = "No Eligible Channel"


@dataclass(frozen=True)
class ResidentProfile:
    """One resident from the unchanged Master Dataset, Residents sheet."""
    resident_id: str
    zone: str
    age: int
    elderly_65_plus: bool
    hearing_impairment: bool
    visual_impairment: bool
    limited_internet: bool
    weak_mobile_coverage: bool
    emergency_app_installed: bool
    in_siren_area: bool
    in_signage_area: bool
    sms_failed_ev01: bool
    voice_usable: bool
    signage_readable: bool
    policy_age_60_plus: bool

    def __post_init__(self) -> None:
        if not self.resident_id:
            raise ValueError("resident_id is required")
        if self.zone not in ("Zone A", "Zone B", "Zone C"):
            raise ValueError("zone must be Zone A, B or C")
        if type(self.age) is not int or self.age < 0:
            raise ValueError("age must be a non-negative integer")
        for name in (
            "elderly_65_plus", "hearing_impairment", "visual_impairment",
            "limited_internet", "weak_mobile_coverage", "emergency_app_installed",
            "in_siren_area", "in_signage_area", "sms_failed_ev01",
            "voice_usable", "signage_readable", "policy_age_60_plus",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        if self.elderly_65_plus != (self.age >= 65):
            raise ValueError("elderly_65_plus must match age")
        if self.policy_age_60_plus != (self.age >= 60):
            raise ValueError("policy_age_60_plus must match age")


@dataclass(frozen=True)
class PlanAssignment:
    """Plan-level selection; no eligible channel is NOT a delivery status."""
    resident_id: str
    plan_id: str
    assignment_status: AssignmentStatus
    selected_channel: ChannelID | None
    reason: str

    def __post_init__(self) -> None:
        if not self.resident_id or not self.plan_id or not self.reason:
            raise ValueError("resident_id, plan_id and reason are required")
        if not isinstance(self.assignment_status, AssignmentStatus):
            raise TypeError("assignment_status must be AssignmentStatus")
        if self.assignment_status == AssignmentStatus.ASSIGNED and not isinstance(self.selected_channel, ChannelID):
            raise ValueError("Assigned plan requires selected_channel")
        if self.assignment_status == AssignmentStatus.NO_ELIGIBLE_CHANNEL and self.selected_channel is not None:
            raise ValueError("No Eligible Channel cannot have a selected channel")


@dataclass(frozen=True)
class Agent1Input:
    configuration: SimulationConfiguration
    residents: tuple[ResidentProfile, ...]
    assignments: tuple[PlanAssignment, ...]
    plan_id: str = "P0"

    def __post_init__(self) -> None:
        if not isinstance(self.configuration, SimulationConfiguration):
            raise TypeError("configuration must be SimulationConfiguration")
        if not self.plan_id:
            raise ValueError("plan_id is required")
        if not isinstance(self.residents, tuple) or any(not isinstance(r, ResidentProfile) for r in self.residents):
            raise TypeError("residents must be a tuple of ResidentProfile")
        if not isinstance(self.assignments, tuple) or any(not isinstance(a, PlanAssignment) for a in self.assignments):
            raise TypeError("assignments must be a tuple of PlanAssignment")
        ids = [resident.resident_id for resident in self.residents]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate resident IDs")
        assignment_ids = [assignment.resident_id for assignment in self.assignments]
        if len(assignment_ids) != len(set(assignment_ids)):
            raise ValueError("Duplicate plan assignments")
        if set(ids) != set(assignment_ids):
            raise ValueError("Each resident needs exactly one plan assignment")
        if any(assignment.plan_id != self.plan_id for assignment in self.assignments):
            raise ValueError("Assignment plan_id mismatch")
        if any(assignment.selected_channel not in self.configuration.enabled_channels
               for assignment in self.assignments if assignment.selected_channel is not None):
            raise ValueError("Selected channel must be planner-enabled")
        # Resident-count completeness against the fixed 1,000 is checked at the
        # orchestration/loader boundary, not in small unit-test fixtures.


@dataclass(frozen=True)
class DeliveryRecord:
    """One resident/channel evaluation. Potential records are never actual attempts."""
    resident_id: str
    plan_id: str
    channel_id: ChannelID
    status: DeliveryStatus
    selected_in_plan: bool
    attempted: bool
    attempt_time_seconds: int | None
    arrival_time_seconds: int | None
    reason: str
    evidence: str

    def __post_init__(self) -> None:
        if not self.resident_id or not self.plan_id or not self.reason or not self.evidence:
            raise ValueError("IDs, reason and evidence are required")
        if not isinstance(self.channel_id, ChannelID) or not isinstance(self.status, DeliveryStatus):
            raise TypeError("Invalid channel or delivery status")
        if type(self.selected_in_plan) is not bool or type(self.attempted) is not bool:
            raise TypeError("selected_in_plan and attempted must be bool")
        if not self.selected_in_plan and self.attempted:
            raise ValueError("Potential channel cannot count as an actual attempt")
        if self.attempted and self.attempt_time_seconds is None:
            raise ValueError("Attempted delivery requires attempt_time_seconds")
        if not self.attempted and self.attempt_time_seconds is not None:
            raise ValueError("Non-attempted evaluation must not have an attempt timestamp")
        for value in (self.attempt_time_seconds, self.arrival_time_seconds):
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("Times must be non-negative integer seconds or None")
        if self.status == DeliveryStatus.UNAVAILABLE:
            if self.attempted or self.arrival_time_seconds is not None:
                raise ValueError("Unavailable means no attempt and no arrival")
            return
        if self.selected_in_plan and not self.attempted:
            raise ValueError("A selected available channel must have an actual attempt")
        if self.status in (DeliveryStatus.DELIVERED, DeliveryStatus.DELAYED):
            if self.arrival_time_seconds is None:
                raise ValueError("Arrival status requires arrival_time_seconds")
            # arrival_time_seconds is the elapsed time after the attempt.
            if self.status == DeliveryStatus.DELIVERED and self.arrival_time_seconds > ON_TIME_DEADLINE_SECONDS:
                raise ValueError("Delivered requires arrival in 0..30 seconds")
            if self.status == DeliveryStatus.DELAYED and not (ON_TIME_DEADLINE_SECONDS < self.arrival_time_seconds <= OBSERVATION_WINDOW_SECONDS):
                raise ValueError("Delayed requires arrival in 31..60 seconds")
        elif self.status == DeliveryStatus.FAILED:
            if self.arrival_time_seconds is not None:
                raise ValueError("Failed must have no arrival within the observation window")


@dataclass(frozen=True)
class Agent1Output:
    plan_id: str
    selected_delivery_records: tuple[DeliveryRecord, ...]
    potential_channel_evaluations: tuple[DeliveryRecord, ...]
    no_eligible_assignments: tuple[PlanAssignment, ...]

    def __post_init__(self) -> None:
        if not self.plan_id:
            raise ValueError("plan_id is required")
        for field_name in ("selected_delivery_records", "potential_channel_evaluations", "no_eligible_assignments"):
            if not isinstance(getattr(self, field_name), tuple):
                raise TypeError(f"{field_name} must be a tuple")
        if any(not isinstance(item, DeliveryRecord) for item in (*self.selected_delivery_records, *self.potential_channel_evaluations)):
            raise TypeError("delivery collections must contain DeliveryRecord instances")
        if any(not isinstance(item, PlanAssignment) for item in self.no_eligible_assignments):
            raise TypeError("no_eligible_assignments must contain PlanAssignment instances")
        if any(not record.selected_in_plan for record in self.selected_delivery_records):
            raise ValueError("Selected results must have selected_in_plan=True")
        if any(record.selected_in_plan or record.attempted for record in self.potential_channel_evaluations):
            raise ValueError("Potential evaluations must be unselected and not attempted")
        if any(item.assignment_status != AssignmentStatus.NO_ELIGIBLE_CHANNEL
               for item in self.no_eligible_assignments):
            raise ValueError("Only No Eligible Channel assignments belong here")
        if any(item.plan_id != self.plan_id for item in self.no_eligible_assignments):
            raise ValueError("Assignment plan_id mismatch")
        if any(item.plan_id != self.plan_id for item in (*self.selected_delivery_records, *self.potential_channel_evaluations)):
            raise ValueError("Delivery record plan_id mismatch")
        selected_keys = [(r.resident_id, r.channel_id) for r in self.selected_delivery_records]
        potential_keys = [(r.resident_id, r.channel_id) for r in self.potential_channel_evaluations]
        if len(selected_keys) != len(set(selected_keys)) or len(potential_keys) != len(set(potential_keys)):
            raise ValueError("Duplicate resident/channel records in a plan are not permitted")
        if set(selected_keys) & set(potential_keys):
            raise ValueError("A resident/channel cannot be both selected and potential in one plan")
        no_eligible_ids = [a.resident_id for a in self.no_eligible_assignments]
        if len(no_eligible_ids) != len(set(no_eligible_ids)):
            raise ValueError("Duplicate No Eligible Channel assignments")
        if set(no_eligible_ids) & {r.resident_id for r in self.selected_delivery_records}:
            raise ValueError("No Eligible Channel cannot have selected delivery records")

    def validate_against_input(self, agent_input: Agent1Input) -> None:
        """Validate handoff consistency; requires input because output alone lacks assignments."""
        if not isinstance(agent_input, Agent1Input):
            raise TypeError("agent_input must be Agent1Input")
        if agent_input.plan_id != self.plan_id:
            raise ValueError("Input and output plan IDs differ")
        assignments = {item.resident_id: item for item in agent_input.assignments}
        enabled = set(agent_input.configuration.enabled_channels)
        for r in (*self.selected_delivery_records, *self.potential_channel_evaluations):
            if r.resident_id not in assignments:
                raise ValueError("Output record references an unknown resident")
            if r.channel_id not in enabled:
                raise ValueError("Output record uses a planner-disabled channel")
            selected = assignments[r.resident_id].selected_channel
            if r.selected_in_plan and r.channel_id != selected:
                raise ValueError("Selected record conflicts with assigned channel")
            if not r.selected_in_plan and r.channel_id == selected:
                raise ValueError("Potential record duplicates the assigned channel")
        expected_no_eligible = {a.resident_id for a in agent_input.assignments
                                if a.assignment_status == AssignmentStatus.NO_ELIGIBLE_CHANNEL}
        actual_no_eligible = {a.resident_id for a in self.no_eligible_assignments}
        if actual_no_eligible != expected_no_eligible:
            raise ValueError("No Eligible Channel output does not match input")
        if any(assignments[a.resident_id] != a for a in self.no_eligible_assignments):
            raise ValueError("No Eligible Channel details do not match input")
        # In P0 there is one selected channel per assigned resident.
        # Recovered plans may support multiple attempts, so full plan completeness
        # belongs to the orchestration layer rather than this generic schema.

    @property
    def actual_attempt_count(self) -> int:
        return sum(record.attempted for record in self.selected_delivery_records)

    @property
    def unique_technical_arrivals(self) -> int:
        return len({record.resident_id for record in self.selected_delivery_records
                    if record.attempted and record.status in (DeliveryStatus.DELIVERED, DeliveryStatus.DELAYED)})
# Step 2.2 — Agents 2–4: interfaces only (no agent inference or simulation).

class RiskPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class AccessibilityStatus(str, Enum):
    USABLE = "Usable in Simulation"
    BARRIER = "Accessibility Barrier"
    REVIEW = "Needs Further Review"
    NOT_ASSESSED = "Not Assessed—No Delivery"


class PolicyCheckStatus(str, Enum):
    NO_ISSUE = "No Issue Identified"
    REVIEW_REQUIRED = "Review Required"
    INSUFFICIENT_INFO = "Insufficient Information"
    NOT_APPLICABLE = "Not Applicable"


class EvidenceKind(str, Enum):
    VERIFIED_SOURCE = "Verified Source"
    SCENARIO_ASSUMPTION = "Synthetic Scenario Assumption"
    UNRESOLVED = "Unresolved Legal Question"
    SIMULATION_RECORD = "Simulation Record"


class RecoveryOutcome(str, Enum):
    PLAN_SELECTED = "Plan Selected"
    NO_SUITABLE_PLAN = "No Suitable Recovery Plan Found"


def _require_nonempty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_tuple_of(value: tuple, typ: type, name: str) -> None:
    if not isinstance(value, tuple) or any(not isinstance(x, typ) for x in value):
        raise TypeError(f"{name} must be tuple[{typ.__name__}, ...]")


@dataclass(frozen=True)
class EvidenceReference:
    reference_id: str
    description: str
    kind: EvidenceKind

    def __post_init__(self) -> None:
        _require_nonempty(self.reference_id, "reference_id")
        _require_nonempty(self.description, "description")
        if not isinstance(self.kind, EvidenceKind):
            raise TypeError("kind must be EvidenceKind")


@dataclass(frozen=True)
class ResidentRiskFinding:
    resident_id: str
    priority: RiskPriority
    reason: str
    accessibility_review_needed: bool
    evidence: tuple[EvidenceReference, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.resident_id, "resident_id")
        _require_nonempty(self.reason, "reason")
        if not isinstance(self.priority, RiskPriority):
            raise TypeError("priority must be RiskPriority")
        if type(self.accessibility_review_needed) is not bool:
            raise TypeError("accessibility_review_needed must be bool")
        _require_tuple_of(self.evidence, EvidenceReference, "evidence")
        if not self.evidence:
            raise ValueError("risk finding requires evidence")


@dataclass(frozen=True)
class Agent2Input:
    configuration: SimulationConfiguration
    agent1_input: Agent1Input
    delivery_results: Agent1Output

    def __post_init__(self) -> None:
        if not isinstance(self.configuration, SimulationConfiguration) or not isinstance(self.agent1_input, Agent1Input) or not isinstance(self.delivery_results, Agent1Output):
            raise TypeError("Agent2Input must contain configuration, Agent1Input, Agent1Output")
        if self.configuration != self.agent1_input.configuration:
            raise ValueError("Agent 2 configuration mismatch")
        self.delivery_results.validate_against_input(self.agent1_input)


@dataclass(frozen=True)
class Agent2Output:
    plan_id: str
    resident_risks: tuple[ResidentRiskFinding, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.plan_id, "plan_id")
        _require_tuple_of(self.resident_risks, ResidentRiskFinding, "resident_risks")
        ids = [x.resident_id for x in self.resident_risks]
        if len(ids) != len(set(ids)):
            raise ValueError("Risk finding per resident must be unique")

    def validate_against_input(self, value: Agent2Input, *, require_complete: bool = False) -> None:
        if not isinstance(value, Agent2Input) or self.plan_id != value.delivery_results.plan_id:
            raise ValueError("Agent 2 plan mismatch")
        known = {x.resident_id for x in value.agent1_input.residents}
        actual = {x.resident_id for x in self.resident_risks}
        if not actual <= known:
            raise ValueError("Risk output references unknown resident")
        if require_complete and actual != known:
            raise ValueError("Risk findings must cover all residents")
        # Priority is computed from selected arrivals only; this checks invariants,
        # not algorithmic explanation quality or accessibility review judgment.
        selected = value.delivery_results.selected_delivery_records
        grouped: dict[str, list[DeliveryRecord]] = {}
        for record in selected:
            grouped.setdefault(record.resident_id, []).append(record)
        for finding in self.resident_risks:
            actual_arrivals = [x for x in grouped.get(finding.resident_id, [])
                               if x.attempted and x.status in (DeliveryStatus.DELIVERED, DeliveryStatus.DELAYED)]
            if any(x.status == DeliveryStatus.DELIVERED for x in actual_arrivals):
                expected = RiskPriority.LOW
            elif actual_arrivals:
                expected = RiskPriority.MEDIUM
            else:
                expected = RiskPriority.HIGH
            if finding.priority != expected:
                raise ValueError(f"Risk priority conflicts with selected arrivals: {finding.resident_id}")


@dataclass(frozen=True)
class AccessibilityFinding:
    resident_id: str
    channel_id: ChannelID | None
    status: AccessibilityStatus
    reason: str
    actionable: bool | None
    evidence: tuple[EvidenceReference, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.resident_id, "resident_id")
        _require_nonempty(self.reason, "reason")
        if self.channel_id is not None and not isinstance(self.channel_id, ChannelID):
            raise TypeError("channel_id must be ChannelID or None")
        if not isinstance(self.status, AccessibilityStatus):
            raise TypeError("status must be AccessibilityStatus")
        if self.actionable is not None and type(self.actionable) is not bool:
            raise TypeError("actionable must be bool or None")
        _require_tuple_of(self.evidence, EvidenceReference, "evidence")
        if self.status == AccessibilityStatus.NOT_ASSESSED and self.actionable is not None:
            raise ValueError("No delivery cannot establish actionability")
        if self.status == AccessibilityStatus.REVIEW and self.actionable is True:
            raise ValueError("Needs Further Review cannot imply confirmed actionability")
        if self.channel_id == ChannelID.PUBLIC_SIRENS and self.actionable is True:
            raise ValueError("Sirens alone are alert-only in this MVP")


@dataclass(frozen=True)
class PolicyFinding:
    check_type: str  # Authorization or Privacy, independently recorded
    status: PolicyCheckStatus
    reason: str
    evidence: tuple[EvidenceReference, ...]
    plan_id: str

    def __post_init__(self) -> None:
        if self.check_type not in ("Authorization", "Privacy"):
            raise ValueError("check_type must be Authorization or Privacy")
        if not isinstance(self.status, PolicyCheckStatus):
            raise TypeError("status must be PolicyCheckStatus")
        _require_nonempty(self.reason, "reason")
        _require_nonempty(self.plan_id, "plan_id")
        _require_tuple_of(self.evidence, EvidenceReference, "evidence")
        if not self.evidence:
            raise ValueError("Policy findings require traceable evidence")


@dataclass(frozen=True)
class CAPAdvisory:
    note: str
    source_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonempty(self.note, "note")
        if not isinstance(self.source_ids, tuple) or any(not isinstance(s, str) or not s.strip() for s in self.source_ids):
            raise ValueError("source_ids must be a tuple of source IDs")
        if not self.source_ids:
            raise ValueError("CAP advisory requires references")
        # No CAP compliance boolean/pass-fail is defined by design.


@dataclass(frozen=True)
class Agent3Input:
    configuration: SimulationConfiguration
    agent1_input: Agent1Input
    delivery_results: Agent1Output
    risk_results: Agent2Output
    warning_fixture_id: str
    actionability_rules_id: str
    source_registry_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.configuration, SimulationConfiguration) or not isinstance(self.agent1_input, Agent1Input) or not isinstance(self.delivery_results, Agent1Output) or not isinstance(self.risk_results, Agent2Output):
            raise TypeError("Agent3Input contains invalid agent handoffs")
        if self.configuration != self.agent1_input.configuration or self.delivery_results.plan_id != self.risk_results.plan_id:
            raise ValueError("Agent 3 input configuration/plan mismatch")
        self.delivery_results.validate_against_input(self.agent1_input)
        for name in ("warning_fixture_id", "actionability_rules_id", "source_registry_id"):
            _require_nonempty(getattr(self, name), name)


@dataclass(frozen=True)
class Agent3Output:
    plan_id: str
    accessibility_findings: tuple[AccessibilityFinding, ...]
    policy_findings: tuple[PolicyFinding, ...]
    cap_advisory: CAPAdvisory | None

    def __post_init__(self) -> None:
        _require_nonempty(self.plan_id, "plan_id")
        _require_tuple_of(self.accessibility_findings, AccessibilityFinding, "accessibility_findings")
        _require_tuple_of(self.policy_findings, PolicyFinding, "policy_findings")
        if self.cap_advisory is not None and not isinstance(self.cap_advisory, CAPAdvisory):
            raise TypeError("cap_advisory must be CAPAdvisory or None")
        if any(x.plan_id != self.plan_id for x in self.policy_findings):
            raise ValueError("Policy finding plan mismatch")
        names = [x.check_type for x in self.policy_findings]
        if len(names) != len(set(names)):
            raise ValueError("Authorization and Privacy are separate unique findings per plan")
        if len({(x.resident_id, x.channel_id) for x in self.accessibility_findings}) != len(self.accessibility_findings):
            raise ValueError("Duplicate accessibility assessment")

    def validate_against_input(self, value: Agent3Input) -> None:
        if not isinstance(value, Agent3Input) or self.plan_id != value.delivery_results.plan_id:
            raise ValueError("Agent 3 plan mismatch")
        selected = {(x.resident_id, x.channel_id): x for x in value.delivery_results.selected_delivery_records}
        assignments = {x.resident_id: x for x in value.agent1_input.assignments}
        for finding in self.accessibility_findings:
            if finding.resident_id not in assignments:
                raise ValueError("Unknown resident in accessibility assessment")
            record = selected.get((finding.resident_id, finding.channel_id))
            arrived = record is not None and record.attempted and record.status in (DeliveryStatus.DELIVERED, DeliveryStatus.DELAYED)
            if finding.status == AccessibilityStatus.NOT_ASSESSED and arrived:
                raise ValueError("Arrived selected delivery cannot be labeled No Delivery")
            if finding.status != AccessibilityStatus.NOT_ASSESSED and not arrived:
                raise ValueError("Accessibility usability verdict requires selected arrival")


@dataclass(frozen=True)
class PlanMetrics:
    plan_id: str
    estimated_reach_count: int
    effective_coverage_count: int
    unresolved_critical_count: int
    actual_selected_attempts: int
    resolved_accessibility_gaps: int

    def __post_init__(self) -> None:
        _require_nonempty(self.plan_id, "plan_id")
        for name in ("estimated_reach_count", "effective_coverage_count", "unresolved_critical_count", "actual_selected_attempts", "resolved_accessibility_gaps"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.estimated_reach_count > RESIDENT_COUNT or self.effective_coverage_count > self.estimated_reach_count:
            raise ValueError("Coverage must be unique, within population, and effective <= estimated")
        if self.unresolved_critical_count > RESIDENT_COUNT or self.resolved_accessibility_gaps > RESIDENT_COUNT:
            raise ValueError("Counts must not exceed resident population")


@dataclass(frozen=True)
class RecoveryCandidate:
    plan_id: str
    assignments: tuple[PlanAssignment, ...]
    feasible: bool
    authorization_status: PolicyCheckStatus
    reason: str
    tested_metrics: PlanMetrics | None = None

    def __post_init__(self) -> None:
        if self.plan_id not in ("P1", "P2", "P3"):
            raise ValueError("Candidate plan ID must be P1–P3")
        _require_tuple_of(self.assignments, PlanAssignment, "assignments")
        if type(self.feasible) is not bool or not isinstance(self.authorization_status, PolicyCheckStatus):
            raise TypeError("Invalid candidate feasibility or authorization status")
        _require_nonempty(self.reason, "reason")
        if any(x.plan_id != self.plan_id for x in self.assignments):
            raise ValueError("Candidate assignment plan ID mismatch")
        ids = [x.resident_id for x in self.assignments]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate candidate resident assignments")
        if self.tested_metrics is not None:
            if not isinstance(self.tested_metrics, PlanMetrics) or self.tested_metrics.plan_id != self.plan_id:
                raise ValueError("Candidate metrics mismatch")
            if not self.feasible or self.authorization_status != PolicyCheckStatus.NO_ISSUE:
                raise ValueError("Untestable candidate must not have simulation metrics")


@dataclass(frozen=True)
class Agent4Input:
    configuration: SimulationConfiguration
    baseline_metrics: PlanMetrics
    baseline_risks: Agent2Output
    baseline_assessment: Agent3Output
    residents: tuple[ResidentProfile, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.configuration, SimulationConfiguration) or not isinstance(self.baseline_metrics, PlanMetrics) or not isinstance(self.baseline_risks, Agent2Output) or not isinstance(self.baseline_assessment, Agent3Output):
            raise TypeError("Invalid Agent4Input handoffs")
        if (self.baseline_metrics.plan_id, self.baseline_risks.plan_id, self.baseline_assessment.plan_id) != ("P0", "P0", "P0"):
            raise ValueError("Agent 4 baseline must be P0")
        _require_tuple_of(self.residents, ResidentProfile, "residents")


@dataclass(frozen=True)
class Agent4Output:
    outcome: RecoveryOutcome
    recommended_plan_id: str
    baseline_metrics: PlanMetrics
    candidates: tuple[RecoveryCandidate, ...]
    final_metrics: PlanMetrics
    explanation: str
    unresolved_review_notes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, RecoveryOutcome):
            raise TypeError("Invalid recovery outcome")
        if self.recommended_plan_id not in ("P0", "P1", "P2", "P3"):
            raise ValueError("Invalid recommended plan ID")
        if not isinstance(self.baseline_metrics, PlanMetrics) or not isinstance(self.final_metrics, PlanMetrics):
            raise TypeError("Recovery metrics must be PlanMetrics")
        if self.baseline_metrics.plan_id != "P0" or self.final_metrics.plan_id != self.recommended_plan_id:
            raise ValueError("Final metrics must match recommended plan")
        _require_tuple_of(self.candidates, RecoveryCandidate, "candidates")
        if len(self.candidates) > 3 or len({x.plan_id for x in self.candidates}) != len(self.candidates):
            raise ValueError("At most three unique recovery candidates are permitted")
        _require_nonempty(self.explanation, "explanation")
        if not isinstance(self.unresolved_review_notes, tuple) or any(not isinstance(x, str) for x in self.unresolved_review_notes):
            raise TypeError("unresolved_review_notes must be tuple of strings")
        candidates_by_id = {x.plan_id: x for x in self.candidates}
        if self.outcome == RecoveryOutcome.NO_SUITABLE_PLAN:
            if self.recommended_plan_id != "P0" or self.final_metrics != self.baseline_metrics:
                raise ValueError("No suitable recovery must retain P0")
        else:
            selected = candidates_by_id.get(self.recommended_plan_id)
            if selected is None or selected.tested_metrics != self.final_metrics:
                raise ValueError("Recommended plan must be a tested candidate")
        if self.final_metrics.effective_coverage_count < self.baseline_metrics.effective_coverage_count:
            raise ValueError("Recovery must not regress baseline effective coverage")

    @property
    def recovery_improvement_percentage_points(self) -> float:
        return 100.0 * (self.final_metrics.effective_coverage_count - self.baseline_metrics.effective_coverage_count) / RESIDENT_COUNT

    def validate_against_input(self, value: Agent4Input) -> None:
        if not isinstance(value, Agent4Input) or self.baseline_metrics != value.baseline_metrics:
            raise ValueError("Recovery baseline differs from input")
        enabled = set(value.configuration.enabled_channels)
        known = {x.resident_id for x in value.residents}
        for candidate in self.candidates:
            for assignment in candidate.assignments:
                if assignment.resident_id not in known:
                    raise ValueError("Candidate references unknown resident")
                if assignment.selected_channel is not None and assignment.selected_channel not in enabled:
                    raise ValueError("Recovery cannot enable planner-disabled channels")

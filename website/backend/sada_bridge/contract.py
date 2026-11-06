"""Explicit web-to-engine contract, grounded in SADA planning-state.ts and schemas.py."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, model_validator
from lastmile_ai.schemas import ChannelID, EventStage, SimulationConfiguration, SCENARIO_ID

WebStage = Literal['T+00', 'T+02', 'T+04', 'T+06']
WebChannel = Literal['CH01', 'CH02', 'CH03', 'CH04', 'CH05']

TO_ENGINE = {
    'T+00': EventStage.T00,
    'T+02': EventStage.T02,
    'T+04': EventStage.T04,
    'T+06': EventStage.T06,
}
TO_WEB = {stage: short for short, stage in TO_ENGINE.items()}

class EvaluationRequest(BaseModel):
    """Request is exactly the existing React SimulationConfig shape."""
    model_config = ConfigDict(extra='forbid', strict=True)
    scenario: Literal['AL_WADI_FLASH_FLOOD']
    stage: WebStage
    enabledChannelIds: list[WebChannel]

    @model_validator(mode='after')
    def validate_channels(self):
        if not self.enabledChannelIds:
            raise ValueError('At least one enabled channel is required')
        if len(self.enabledChannelIds) != len(set(self.enabledChannelIds)):
            raise ValueError('Duplicate channel IDs are forbidden')
        return self

    def to_engine_configuration(self) -> SimulationConfiguration:
        if self.scenario != SCENARIO_ID:
            raise ValueError('Unexpected scenario')
        return SimulationConfiguration(
            selected_stage=TO_ENGINE[self.stage],
            enabled_channels=tuple(ChannelID(id) for id in self.enabledChannelIds),
        )

    def canonical_web_config(self) -> dict:
        # Stable ChannelID order reflects the engine's already-validated configuration.
        engine = self.to_engine_configuration()
        return {
            'scenario': SCENARIO_ID,
            'stage': TO_WEB[engine.selected_stage],
            'enabledChannelIds': [id.value for id in engine.enabled_channels],
        }

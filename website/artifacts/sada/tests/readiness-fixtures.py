"""Read-only original-engine fixtures: no HTTP, database or inference calls."""
import json
import socket
import sys
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend"))


def no_network(*args, **kwargs):
    raise RuntimeError("Network prohibited in readiness engine regressions")


socket.create_connection = no_network
socket.socket.connect = no_network
socket.socket.connect_ex = no_network

from sada_bridge.contract import EvaluationRequest
from sada_bridge.normalize import normalize_result
from lastmile_ai.agents.ethar_stage_bridge import run_ethar_integrated_recovery

cases = [
    ("T+00", ["CH01"]),
    ("T+02", ["CH02", "CH03"]),
    ("T+04", ["CH01", "CH02", "CH03", "CH04", "CH05"]),
    ("T+06", ["CH04", "CH05"]),
]
results = []
for stage, channels in cases:
    config = EvaluationRequest(
        scenario="AL_WADI_FLASH_FLOOD", stage=stage, enabledChannelIds=channels
    ).to_engine_configuration()
    run = run_ethar_integrated_recovery(config)
    results.append(normalize_result(run, config, str(uuid5(NAMESPACE_URL, f"sada-readiness-test-{stage}"))))
print(json.dumps(results, ensure_ascii=False))

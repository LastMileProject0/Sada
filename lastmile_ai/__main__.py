"""Start-up smoke check; does not execute the LastMile simulation."""
import argparse
import json
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def verify_setup() -> dict:
    root = project_root()
    cfg_path = root / "config" / "bootstrap.json"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Missing bootstrap configuration: {cfg_path}")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert cfg["synthetic_residents"] == 1000, "Approved population must remain 1,000"
    assert cfg["baseline_priority"] == ["CH01", "CH03", "CH02", "CH04", "CH05"], "P0 order differs from Step 1"
    assert cfg["timely_seconds"] == 30 and cfg["observation_seconds"] == 60, "Timing does not match Step 1"
    assert len(cfg["channels"]) == 5, "Approved five-channel scenario only"
    assert cfg["example_stage"] in cfg["selectable_stages"], "Invalid example stage"
    assert set(cfg["example_enabled_channels"]) <= set(cfg["channels"]), "Unknown channel"
    assert len(cfg["example_enabled_channels"]) >= 1, "One channel must be enabled"
    assert cfg["max_recovery_candidates"] == 3, "Candidate limit differs from Step 1"
    workbook = root / "data" / "reference" / "LastMile_AI_Step1_Master_Dataset.xlsx"
    master_doc = root / "docs" / "reference" / "LastMile_AI_Step1_Master_Document.docx"
    assert workbook.is_file(), f"Missing approved workbook: {workbook}"
    assert master_doc.is_file(), f"Missing approved master document: {master_doc}"
    return cfg


def main() -> int:
    parser = argparse.ArgumentParser(description="LastMile AI Step 2 project startup")
    parser.add_argument("--check", action="store_true", help="Validate project setup and approved reference presence")
    args = parser.parse_args()
    try:
        cfg = verify_setup()
    except (AssertionError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"PROJECT SETUP: FAIL — {exc}")
        return 1
    print("PROJECT SETUP: PASS")
    print(f"Scenario: {cfg['scenario']} — {cfg['synthetic_residents']} SYNTHETIC residents")
    print("Enabled example channels: " + ", ".join(cfg["example_enabled_channels"]))
    print("Agents/simulation/coverage metrics: NOT IMPLEMENTED YET (team Step 2 deliverables)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

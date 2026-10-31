
"""Step 4 - Reproducible LastMile AI Demo Runner."""

import argparse
import sys
from pathlib import Path

# Allow running the script directly from the repository.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from lastmile_ai.schemas import (
    ChannelID,
    EventStage,
    SimulationConfiguration,
)
from lastmile_ai.recovery_runtime import run_integrated_recovery
from lastmile_ai.dashboard import build_dashboard
from lastmile_ai.report import build_report


STAGES = {
    "T+00": EventStage.T00,
    "T+02": EventStage.T02,
    "T+04": EventStage.T04,
    "T+06": EventStage.T06,
}


def parse_channel_codes(values):
    """Read channel IDs supplied as spaces or comma-separated values."""
    return [
        code.strip().upper()
        for value in (values or [])
        for code in value.split(",")
        if code.strip()
    ]


def make_configuration(stage, channels=None, disabled=None):
    """Validate the planner's selected stage and enabled channels."""

    if stage not in STAGES:
        raise ValueError("Invalid event stage")

    if channels is None:
        selected = [channel.value for channel in ChannelID]
    else:
        selected = parse_channel_codes(channels)

    disabled_codes = parse_channel_codes(disabled)

    valid_codes = {channel.value for channel in ChannelID}

    unknown = (
        set(selected) | set(disabled_codes)
    ) - valid_codes

    if unknown:
        raise ValueError(
            f"Invalid channel IDs: {sorted(unknown)}"
        )

    if len(selected) != len(set(selected)):
        raise ValueError("Duplicate enabled channels")

    enabled_codes = set(selected) - set(disabled_codes)

    if not enabled_codes:
        raise ValueError(
            "At least one channel must remain enabled"
        )

    enabled_channels = tuple(
        channel
        for channel in ChannelID
        if channel.value in enabled_codes
    )

    return SimulationConfiguration(
        selected_stage=STAGES[stage],
        enabled_channels=enabled_channels,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="LastMile AI - Step 4 Demo Runner"
    )

    parser.add_argument(
        "--stage",
        choices=list(STAGES),
        default="T+02",
        help="Choose T+00, T+02, T+04 or T+06",
    )

    parser.add_argument(
        "--channels",
        nargs="+",
        default=None,
        help="Enable specific channels, e.g. CH01 CH03",
    )

    parser.add_argument(
        "--disable",
        nargs="+",
        default=[],
        help="Disable channels, e.g. CH02 CH05",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("demo_output"),
        help="Directory for generated HTML and Markdown files",
    )

    args = parser.parse_args(argv)

    try:
        configuration = make_configuration(
            stage=args.stage,
            channels=args.channels,
            disabled=args.disable,
        )
    except ValueError as error:
        parser.error(str(error))

    # Run the real integrated Step 3 agents.
    result = run_integrated_recovery(configuration)

    # Generate outputs from actual simulation results.
    dashboard_html = build_dashboard(result)
    report_markdown = build_report(result)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    dashboard_path = output_dir / "dashboard.html"
    report_path = output_dir / "report.md"

    dashboard_path.write_text(
        dashboard_html,
        encoding="utf-8",
    )

    report_path.write_text(
        report_markdown,
        encoding="utf-8",
    )

    print("\nLastMile AI - Synthetic Demo")
    print("-------------------------------")
    print("Stage:", configuration.selected_stage.value)

    print(
        "Enabled channels:",
        ", ".join(
            channel.value
            for channel in configuration.enabled_channels
        ),
    )

    print(
        "P0 Effective Coverage:",
        result.baseline.metrics.effective_coverage_count,
    )

    print(
        "Recommended Plan:",
        result.recovery.recommended_plan_id,
    )

    print(
        "Final Effective Coverage:",
        result.recovery.final_metrics.effective_coverage_count,
    )

    print("\nDashboard:", dashboard_path.resolve())
    print("Report:", report_path.resolve())
    print("\nDemo completed successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

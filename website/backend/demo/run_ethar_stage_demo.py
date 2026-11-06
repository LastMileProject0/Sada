"""Optional read-only demo of real Ethar EV02 -> Agent 3/4 integration.

The original demo/run_demo.py is unchanged and still runs the legacy baseline.
This entry point explicitly opts in to Ethar stage evidence, producing the
same dashboard/report formats through the existing renderer.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from demo.run_demo import STAGES, make_configuration
from lastmile_ai.agents.ethar_stage_bridge import run_ethar_integrated_recovery
from lastmile_ai.dashboard import build_dashboard
from lastmile_ai.report import build_report


def main(argv=None) -> int:
    """Run the real stage-aware synthetic demo and write its two reports."""
    parser = argparse.ArgumentParser(description='LastMile AI: Ethar stage-aware recovery demo')
    parser.add_argument('--stage', choices=list(STAGES), default='T+04')
    parser.add_argument('--channels', nargs='+', default=None)
    parser.add_argument('--disable', nargs='+', default=[])
    parser.add_argument('--output-dir', type=Path, default=Path('demo_ethar_output'))
    args = parser.parse_args(argv)
    try:
        config = make_configuration(args.stage, args.channels, args.disable)
    except ValueError as exc:
        parser.error(str(exc))
    run = run_ethar_integrated_recovery(config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    dashboard = args.output_dir / 'dashboard.html'
    report = args.output_dir / 'report.md'
    dashboard.write_text(build_dashboard(run), encoding='utf-8')
    report.write_text(build_report(run), encoding='utf-8')
    print('LastMile AI — Ethar EV02 stage-aware synthetic demo')
    print('Stage:', config.selected_stage.value)
    print('Enabled:', ', '.join(ch.value for ch in config.enabled_channels))
    print('P0 technical reach:', run.baseline.metrics.estimated_reach_count)
    print('P0 effective coverage:', run.baseline.metrics.effective_coverage_count)
    print('Recommended:', run.recovery.recommended_plan_id)
    print('Final technical reach:', run.recovery.final_metrics.estimated_reach_count)
    print('Final effective coverage:', run.recovery.final_metrics.effective_coverage_count)
    print('Dashboard:', dashboard.resolve())
    print('Report:', report.resolve())
    return 0


if __name__ == '__main__':
    sys.exit(main())

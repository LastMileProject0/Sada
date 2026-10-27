"""Step 3: human-readable report from actual Agent 4 results."""
from lastmile_ai.schemas import Agent4Output, RESIDENT_COUNT


def build_report(result: Agent4Output) -> str:
    """Create a Markdown report without claiming compliance or inventing KPIs."""
    if not isinstance(result, Agent4Output):
        raise TypeError("result must be Agent4Output")
    before, after = result.baseline_metrics, result.final_metrics
    improvement = (after.effective_coverage_count - before.effective_coverage_count) / RESIDENT_COUNT * 100
    lines = [
        "# LastMile AI — Simulation Report",
        "", "Simulation only — no real emergency alert was sent.", "",
        "## 1. Accessibility & affected groups",
        "Detailed before/after accessibility group gaps require per-resident Agent 1 and Agent 3 results.",
        "", "## 2. Channel performance",
        "Per-channel deliveries and delays require selected delivery records from Agent 1.",
        "", "## 3. Plan comparison",
        "| Metric | Baseline P0 | Final plan |",
        "|---|---:|---:|",
        f"| Estimated reach | {before.estimated_reach_count} | {after.estimated_reach_count} |",
        f"| Effective warning coverage | {before.effective_coverage_count} | {after.effective_coverage_count} |",
        f"| Unresolved critical cases | {before.unresolved_critical_count} | {after.unresolved_critical_count} |",
        f"| Selected attempts | {before.actual_selected_attempts} | {after.actual_selected_attempts} |",
        f"| Resolved accessibility gaps | {before.resolved_accessibility_gaps} | {after.resolved_accessibility_gaps} |",
        "", f"Recovery improvement: {improvement:.1f} percentage points.",
        "", "## 4. Policy and traceability",
        "Authorization/privacy are scenario assessments, not legal certification. Detailed findings must come from Agent 3.",
        "", "## 5. Final recommendation",
        f"Outcome: {result.outcome.value}",
        f"Recommended plan: {result.recommended_plan_id}",
        f"Explanation: {result.explanation}",
    ]
    if result.unresolved_review_notes:
        lines.extend(["", "Review notes:"] + [f"- {note}" for note in result.unresolved_review_notes])
    return "\n".join(lines) + "\n"

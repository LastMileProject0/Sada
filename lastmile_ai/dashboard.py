"""Step 3: local, static HTML dashboard from actual Agent 4 output."""
from html import escape
from lastmile_ai.schemas import Agent4Output, RESIDENT_COUNT


def build_dashboard(result: Agent4Output) -> str:
    """Return a static HTML summary; no fabricated resident/channel findings."""
    if not isinstance(result, Agent4Output):
        raise TypeError("result must be Agent4Output")
    a, b = result.baseline_metrics, result.final_metrics
    improvement = (b.effective_coverage_count - a.effective_coverage_count) / RESIDENT_COUNT * 100
    cards = (
        ("Estimated Reach", f"{b.estimated_reach_count:,} / {RESIDENT_COUNT:,}"),
        ("Effective Warning Coverage", f"{b.effective_coverage_count:,} / {RESIDENT_COUNT:,}"),
        ("Recovery Improvement", f"{improvement:.1f} percentage points"),
        ("Unresolved Critical Cases", f"{b.unresolved_critical_count:,}"),
    )
    cards_html = "\n".join(
        f'<section class="card"><h2>{escape(title)}</h2><p>{escape(value)}</p></section>'
        for title, value in cards
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>LastMile AI Dashboard</title>
<style>body{{font-family:Arial,sans-serif;background:#f5f7fb;color:#18253a;margin:2rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:1rem}}
.card{{background:white;border-radius:12px;padding:1.2rem;box-shadow:0 1px 6px #0001}}
.card h2{{font-size:1rem}}.card p{{font-size:1.7rem;font-weight:bold}}
.note{{margin-top:1.5rem;max-width:900px;line-height:1.6}}</style></head>
<body><h1>LastMile AI — Simulation Dashboard</h1>
<p>Scenario simulation only. No real warnings sent.</p>
<div class="grid">{cards_html}</div>
<section class="note"><h2>Final recommendation: {escape(result.recommended_plan_id)}</h2>
<p>{escape(result.explanation)}</p>
<p>Before: P0 effective coverage {a.effective_coverage_count:,}; after: {b.effective_coverage_count:,}.</p>
<p>Detailed affected-group and channel-performance views will use Agent 1 and Agent 3 records when integrated.</p>
<p>Policy findings are advisory and are not legal compliance certification.</p></section>
</body></html>'''

# SADA AI — Emergency Warning Resilience Planning

**SADA AI** is a policy-informed, four-agent prototype for **offline, pre-event emergency-warning planning**. It uses 1,000 synthetic resident profiles to compare delivery channels, identify technical and accessibility risks, and evaluate recovery plans across staged scenarios. It is **not** a live alert-dispatch service or a certified emergency-response platform.

**Public website:** [SADA AI demo](https://safe-integration-testing-copy-of-sada.replit.app/)  
**Technical report and submission documents:** [`docs/submission/`](docs/submission/)  
**Reproducible Python demo instructions:** [`demo/README.md`](demo/README.md)

### Submission resources

- [KB reference sources (JSON)](docs/submission/kb_reference_sources.json) — five proposed official reference sources, documented separately from the runtime knowledge base.
- [KB reference schema](docs/submission/kb_reference_schema.md) — general-purpose source metadata and documentation format.
- [Policy and standards gap mapping](docs/submission/policy_gap_mapping.md) — emergency communications, accessibility, transparency and AI-risk comparisons.
- [Four-agent and auditability summary](docs/submission/agents_audit_summary.md) — workflow, evidence handoffs and limitations.
- [T+00 plan-comparison evidence](docs/submission/step4_T00_comparison.md) — a reproducible synthetic example.
- [Final technical report (PDF)](docs/submission/SADA_AI_Final_Technical_Report_With_Mentor.pdf).

**Scope note:** The additional KB JSON is **documentation-only**, not new runtime retrieval content. The prototype's evidence, source references and simulated outcomes do not imply full legal, cybersecurity or accessibility compliance. The demo video link can be added when its final edit is complete.

---

## Technical prototype — LastMile AI (Step 3 integrated simulation)

**AI-Powered Multi-Agent Emergency Communication & Resilience System**  
**Team:** Sereen (integration, metrics, dashboard/report), Ethar (Agent 1), Salma (Agents 2 & 4), Maymona (Agent 3).

## Scope and status

This is an **offline, pre-event planning simulation** using the approved, synthetic 1,000-resident dataset. It does **not** send real warnings, model real cellular network infrastructure, certify Common Alerting Protocol (CAP) compliance, or issue legal authorization/compliance decisions. The canonical Arabic warning fixture is fixed; the prototype chooses/test channels and accessibility assumptions rather than rewriting warning text.

**Step 3 implemented:** Agent 1 delivery, Agent 2 technical risk, Agent 3 accessibility/policy assessment, Agent 4 recovery planning; deterministic P0 vs P1–P3 reruns, KPIs, an HTML dashboard, a five-section Markdown report, and automated tests.

The CLI `--check` validates project setup only. It is **not** a simulation runner.

## Setup and tests

Run from the repository root in PowerShell or a terminal:

```powershell
python -m pip install -r requirements.txt
python -m lastmile_ai --check
python -m unittest discover -s tests -p "test_*.py" -v
```

CI: `.github/workflows/step3-tests.yml` runs the full tests on pushes to the integration branch and `main`, and on pull requests into `main`.

## Generate a real synthetic dashboard and report

The functions below use **all four actual Agent implementations**, not mocked data. For Windows PowerShell, paste the following block from the repository root:

```powershell
@'
from pathlib import Path
from lastmile_ai.schemas import ChannelID, EventStage, SimulationConfiguration
from lastmile_ai.recovery_runtime import run_integrated_recovery
from lastmile_ai.dashboard import build_dashboard
from lastmile_ai.report import build_report

config = SimulationConfiguration(EventStage.T02, tuple(ChannelID))
run = run_integrated_recovery(config)
output = Path("demo_output")
output.mkdir(exist_ok=True)
(output / "dashboard.html").write_text(build_dashboard(run), encoding="utf-8")
(output / "report.md").write_text(build_report(run), encoding="utf-8")
print("P0:", run.baseline.metrics)
print("Final:", run.recovery.final_metrics)
print("Recommended:", run.recovery.recommended_plan_id)
print("Saved:", output.resolve())
'@ | python -
```

Open `demo_output/dashboard.html` in a browser and `demo_output/report.md` with a Markdown viewer. Select a different approved snapshot using `EventStage.T00`, `T02`, `T04`, or `T06`. To limit enabled channels, pass an explicit nonempty tuple such as `(ChannelID.SMS, ChannelID.VOICE_CALL)` in the `SimulationConfiguration`. Always rerun both baseline and recovery under the same settings.

**Key definitions:** Estimated Reach counts selected attempts marked Delivered or Delayed within 60s. Effective Warning Coverage additionally requires an on-time, usable, actionable selected channel. Sirens (CH04) alone are alert-only. Missing evidence remains `Needs Further Review`, not assumed success.

## Main modules

| Location | Role |
|---|---|
| `lastmile_ai/agents/delivery.py`, `scenario_conditions.py` | Agent 1 and scenario conditions |
| `lastmile_ai/agents/risk.py` | Agent 2 risk analysis |
| `lastmile_ai/agents/evaluation.py`, `policy_accessibility.py` | Agent 3 accessibility/policy |
| `lastmile_ai/agents/recovery.py` | Agent 4 proposal / selection |
| `lastmile_ai/runtime.py` | Real P0 execution of Agents 1–3 |
| `lastmile_ai/recovery_runtime.py` | Real comparison of P0 with P1/P2/P3 |
| `lastmile_ai/metrics.py` | Core and supporting KPIs |
| `lastmile_ai/dashboard.py` | Standalone HTML dashboard |
| `lastmile_ai/report.py` | Five-section Markdown report |
| `data/reference/LastMile_AI_Step1_Master_Dataset.xlsx` | Approved immutable input dataset |
| `lastmile_ai/knowledge/` | Fixed Arabic warning and source registry |

The master Step 1 document is in `docs/reference/`; team handoffs and assumptions are in `docs/`. See the committed unit tests for the checked behavior. Demo values are simulated assumptions, not measured emergency-response performance.

## License & Permissions

© 2026 SADA AI Project Contributors. All rights reserved.

**Academic Affiliation:** Al-Balqa Applied University, Faculty of Artificial Intelligence, Jordan.

SADA AI source code is publicly available for viewing, academic review, and project evaluation only.

Modification, reuse, redistribution, commercial use, or incorporation into other projects requires prior written permission from the authorized rights holders.

To request permission, please contact the SADA AI team through GitHub Issues. Permission is not granted unless written approval is received.

See the [LICENSE](LICENSE) file for full terms.

"""Tests for Agent 4. Run: python -m unittest -v test_agent4_runtime.py"""
import unittest
from lastmile_ai.agents.recovery import VerifiedEvaluation, propose_candidates, run_agent4
from lastmile_ai.schemas import (
    Agent4Input, Agent2Output, Agent3Output, ChannelID, EventStage,
    SimulationConfiguration, ResidentProfile, PlanMetrics, PlanAssignment,
    AssignmentStatus, PolicyCheckStatus, RecoveryOutcome,
)


def resident(rid, *, app=True, siren=True, signage=True, voice=True):
    return ResidentProfile(rid, 'Zone A', 30, False, False, False, False, False,
                           app, siren, signage, False, voice, True, False)


def setup(n=3, enabled=None, baseline_covered=None):
    ids = [f'R{i}' for i in range(n)]
    people = tuple(resident(rid) for rid in ids)
    configuration = SimulationConfiguration(EventStage.T02, tuple(enabled or ChannelID))
    covered = frozenset(baseline_covered or ())
    assignments = tuple(PlanAssignment(rid, 'P0', AssignmentStatus.ASSIGNED,
                                      ChannelID.SMS, 'Baseline') for rid in ids)
    metrics = PlanMetrics('P0', len(covered), len(covered), n-len(covered), n, 0)
    value = Agent4Input(configuration, metrics, Agent2Output('P0', ()),
                        Agent3Output('P0', (), (), None), people)
    return value, assignments, covered


def evaluation(candidate, effective, *, authorized=True, safe=True, gaps=0, attempts=3, critical=0):
    metrics = PlanMetrics(candidate.plan_id, len(effective), len(effective),
                          critical, attempts, gaps)
    return VerifiedEvaluation(metrics, frozenset(effective),
                              PolicyCheckStatus.NO_ISSUE if authorized else PolicyCheckStatus.REVIEW_REQUIRED,
                              safe, 'Verified synthetic evaluator')


class Agent4RuntimeTests(unittest.TestCase):
    def test_no_evaluator_never_invents_metrics(self):
        value, assignments, covered = setup()
        out = run_agent4(value, baseline_assignments=assignments, baseline_effective_ids=covered)
        self.assertEqual(out.outcome, RecoveryOutcome.NO_SUITABLE_PLAN)
        self.assertEqual(out.final_metrics, value.baseline_metrics)
        self.assertEqual(len(out.candidates), 3)
        self.assertTrue(all(c.tested_metrics is None for c in out.candidates))

    def test_authorized_verified_improvement_is_selected(self):
        value, assignments, covered = setup(baseline_covered={'R0'})
        def evaluator(c):
            return evaluation(c, {'R0', 'R1'} if c.plan_id == 'P2' else {'R0'}, attempts=3)
        out = run_agent4(value, baseline_assignments=assignments,
                         baseline_effective_ids=covered, evaluate=evaluator)
        self.assertEqual(out.recommended_plan_id, 'P2')
        self.assertEqual(out.final_metrics.effective_coverage_count, 2)

    def test_authorization_blocks_even_high_coverage(self):
        value, assignments, covered = setup()
        out = run_agent4(value, baseline_assignments=assignments,
                         baseline_effective_ids=covered,
                         evaluate=lambda c: evaluation(c, {'R0', 'R1', 'R2'}, authorized=False))
        self.assertEqual(out.recommended_plan_id, 'P0')
        self.assertTrue(all(c.tested_metrics is None for c in out.candidates))

    def test_safety_blocks_candidate(self):
        value, assignments, covered = setup()
        out = run_agent4(value, baseline_assignments=assignments,
                         baseline_effective_ids=covered,
                         evaluate=lambda c: evaluation(c, {'R0'}, safe=False))
        self.assertEqual(out.recommended_plan_id, 'P0')

    def test_per_resident_regression_blocks_candidate(self):
        value, assignments, covered = setup(baseline_covered={'R0'})
        out = run_agent4(value, baseline_assignments=assignments,
                         baseline_effective_ids=covered,
                         evaluate=lambda c: evaluation(c, {'R1', 'R2'}))
        self.assertEqual(out.recommended_plan_id, 'P0')

    def test_tiebreak_accessibility_then_critical_then_coverage(self):
        value, assignments, covered = setup()
        def evaluator(c):
            if c.plan_id == 'P1': return evaluation(c, {'R0','R1','R2'}, gaps=1, critical=0)
            if c.plan_id == 'P2': return evaluation(c, {'R0','R1'}, gaps=2, critical=1)
            return evaluation(c, {'R0'}, gaps=0, critical=0)
        out = run_agent4(value, baseline_assignments=assignments,
                         baseline_effective_ids=covered, evaluate=evaluator)
        self.assertEqual(out.recommended_plan_id, 'P2')

    def test_tiebreak_attempts_then_plan_id(self):
        value, assignments, covered = setup()
        out = run_agent4(value, baseline_assignments=assignments,
                         baseline_effective_ids=covered,
                         evaluate=lambda c: evaluation(c, {'R0'}, attempts=4 if c.plan_id == 'P1' else 3))
        self.assertEqual(out.recommended_plan_id, 'P2')

    def test_proposals_only_enabled_and_preserve_effective(self):
        value, assignments, covered = setup(enabled=(ChannelID.SMS, ChannelID.VOICE_CALL), baseline_covered={'R0'})
        props = propose_candidates(value, assignments, covered)
        self.assertTrue(all(a.selected_channel in {ChannelID.SMS, ChannelID.VOICE_CALL}
                            for p in props for a in p.assignments))
        self.assertTrue(all(p.assignments[0].selected_channel == ChannelID.SMS for p in props))

    def test_invalid_evaluator_counts_rejected(self):
        value, assignments, covered = setup()
        def invalid(c):
            result = evaluation(c, {'R0'})
            return VerifiedEvaluation(PlanMetrics(c.plan_id, 2, 2, 0, 3, 0),
                                      result.effective_resident_ids,
                                      result.authorization_status, True, 'Bad count')
        with self.assertRaises(ValueError):
            run_agent4(value, baseline_assignments=assignments,
                       baseline_effective_ids=covered, evaluate=invalid)

    def test_missing_baseline_roster_rejected(self):
        value, assignments, covered = setup()
        with self.assertRaises(ValueError):
            run_agent4(value, baseline_assignments=assignments[:-1], baseline_effective_ids=covered)


if __name__ == '__main__':
    unittest.main()

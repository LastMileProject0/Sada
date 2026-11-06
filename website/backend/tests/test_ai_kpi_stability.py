"""Verify that invoking the AI sidecar does not change actual deterministic baseline."""
import unittest
from lastmile_ai.ai.policy_explainer import explain_policy
from lastmile_ai.runtime import run_integrated_baseline
from lastmile_ai.schemas import SimulationConfiguration, EventStage, ChannelID


class RealKpiStabilityTests(unittest.TestCase):
    def test_actual_p0_metrics_unchanged_by_ai_sidecar(self):
        """Compare real P0 output before and after read-only explanation."""
        config=SimulationConfiguration(EventStage.T02,tuple(ChannelID))
        first=run_integrated_baseline(config)
        retrieval={'schema_version':'policy_retrieval.v1','query':'Q','method':'lexical',
          'passages':[{'passage_id':'TEST-P1','source_id':'SRC-01','source_title':'Synthetic Test',
            'section':'Synthetic', 'official_url':'https://example.org/test','locator':'Test',
            'source_verified':True,'text':'The synthetic plan has five channels.'}]}
        snapshot=(first.metrics,first.agent1_input.assignments,first.delivery.selected_delivery_records)
        result=explain_policy('Explain this synthetic demonstration.',retrieval,
             provider=lambda p,m:'This is a synthetic demonstration. [TEST-P1]')
        self.assertEqual(result.status,'Answered')
        self.assertEqual(snapshot,(first.metrics,first.agent1_input.assignments,first.delivery.selected_delivery_records))
        second=run_integrated_baseline(config)
        self.assertEqual(first.metrics,second.metrics)
        self.assertEqual(first.agent1_input.assignments,second.agent1_input.assignments)

if __name__=='__main__':unittest.main()

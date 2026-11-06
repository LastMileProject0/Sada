import { CHANNEL_IDS } from './planning-state';
import { evaluationSchema } from './results-model';

// Only the values explicitly confirmed by the user. No other fixture metrics are inferred.
export const verifiedResultsDemo = evaluationSchema.parse({
  id: 'verified-demo-all-channel-t04',
  source: 'verified_demo',
  configuration: {
    scenario: 'AL_WADI_FLASH_FLOOD', stage: 'T+04',
    enabledChannelIds: [...CHANNEL_IDS], population: 1000,
  },
  plans: [
    {
      id: 'P0',
      metrics: {
        reach: { value: 722, unit: 'residents' },
        effective: { value: 0, unit: 'residents' },
        recovery: null, critical: null,
      },
      accessibility: null, channels: [],
    },
    {
      id: 'P3',
      metrics: {
        reach: { value: 942, unit: 'residents' },
        effective: { value: 366, unit: 'residents' },
        recovery: null, critical: null,
      },
      accessibility: null, channels: [],
    },
  ],
  recommendedPlanId: 'P3',
  explanation: null,
});

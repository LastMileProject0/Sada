import path from 'node:path';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  resolve: { alias: { '@': path.resolve(import.meta.dirname, 'src') } },
  esbuild: { jsx: 'automatic' },
  test: {
    environment: 'jsdom',
    include: ['src/**/*.integration.test.ts', 'src/lib/policy-assistant.test.ts'],
    clearMocks: true,
    restoreMocks: true,
  },
});

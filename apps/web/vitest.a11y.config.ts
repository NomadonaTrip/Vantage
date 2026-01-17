import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup-a11y.ts'],
    include: [
      'tests/**/*.a11y.test.{ts,tsx}',
      'tests/a11y/**/*.test.{ts,tsx}',
      'components/**/*.a11y.test.{ts,tsx}',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['components/**/*.tsx'],
      exclude: [
        'components/ui/**', // shadcn components are pre-tested
        '**/*.test.tsx',
        '**/*.d.ts',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});

import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      '**/build/**',
      '**/.wrangler/**',
      '**/.svelte-kit/**',
      '**/.output/**',
      '**/.venv/**',
      '**/.git/**',
      '**/__pycache__/**',
      '**/.pytest_cache/**',
      '**/.mypy_cache/**',
      '**/.ruff_cache/**',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
);

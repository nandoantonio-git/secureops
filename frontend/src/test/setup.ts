import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// @testing-library/react's built-in auto-cleanup only self-registers when it
// detects a global `afterEach` (e.g. Jest, or Vitest with `test.globals:
// true`). This project imports test APIs explicitly instead of using
// Vitest's globals, so that detection never fires -- do it here instead, or
// widget tests leak DOM across `it()` blocks within the same file.
afterEach(() => {
  cleanup();
});

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  }),
});

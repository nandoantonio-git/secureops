import { useEffect, useState } from 'react';

const QUERY = '(prefers-reduced-motion: reduce)';

function readPreference(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }
  return window.matchMedia(QUERY).matches;
}

/**
 * Single source of truth for reduced-motion support, consumed by the
 * skeleton shimmer and both chart widgets so the rule is implemented once,
 * not reinvented per component.
 */
export function usePrefersReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] =
    useState(readPreference);

  useEffect(() => {
    const mediaQuery = window.matchMedia(QUERY);
    const handleChange = () => setPrefersReducedMotion(mediaQuery.matches);
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReducedMotion;
}

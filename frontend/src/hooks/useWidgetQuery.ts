import { useCallback, useEffect, useState } from 'react';

export type WidgetQueryState<T> =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; data: T };

/**
 * Small per-widget loading/error/retry wrapper. Each widget owns its own
 * hook instance, so one widget's failure never touches the other 3 -- a
 * caching library (react-query et al.) would be unjustified weight for 4
 * independent GETs with a manual retry button.
 */
export function useWidgetQuery<T>(
  fetcher: () => Promise<T>,
  deps: readonly unknown[],
): { state: WidgetQueryState<T>; retry: () => void } {
  const [state, setState] = useState<WidgetQueryState<T>>({
    status: 'loading',
  });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading' });

    fetcher()
      .then((data) => {
        if (!cancelled) {
          setState({ status: 'success', data });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            status: 'error',
            message: error instanceof Error ? error.message : String(error),
          });
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, attempt]);

  const retry = useCallback(() => setAttempt((value) => value + 1), []);

  return { state, retry };
}

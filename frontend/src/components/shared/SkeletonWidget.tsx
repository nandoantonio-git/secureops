import { usePrefersReducedMotion } from '../../hooks/usePrefersReducedMotion';

/** Per-widget skeleton, never a full-screen spinner. */
export function SkeletonWidget({ title }: { title: string }) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const blockClass = prefersReducedMotion
    ? 'skeleton-block skeleton-block--static'
    : 'skeleton-block';

  return (
    <div className="widget" aria-busy="true" aria-label={`Carregando ${title}`}>
      <div className={blockClass} style={{ height: '1rem', width: '55%' }} />
      <div className={blockClass} style={{ height: '8rem', marginTop: '1rem' }} />
    </div>
  );
}

import { lazy, Suspense } from 'react';
import { AdvisoryModeBadge } from '../shared/AdvisoryModeBadge';
import { SkeletonWidget } from '../shared/SkeletonWidget';
import { TopCriticalFilesWidget } from './TopCriticalFilesWidget';
import { FindingsListWidget } from './FindingsListWidget';

const SeverityDonutWidget = lazy(() =>
  import('./SeverityDonutWidget').then((module) => ({ default: module.SeverityDonutWidget })),
);
const WeeklyTrendWidget = lazy(() =>
  import('./WeeklyTrendWidget').then((module) => ({ default: module.WeeklyTrendWidget })),
);

const REPOSITORY: string =
  (import.meta.env.VITE_DASHBOARD_REPOSITORY as string | undefined) ?? '';

// The dashboard has no endpoint for gate mode (out of this MVP's scope), so
// this mirrors the backend's GATE_MODE setting via env config instead of
// being queried live. Showing "advisory" when the backend is actually in
// blocking mode would be misleading, so the badge only renders for the
// advisory case rather than asserting a state that might be wrong.
const GATE_MODE: string =
  (import.meta.env.VITE_DASHBOARD_GATE_MODE as string | undefined) ?? 'advisory';

export function SecurityOverviewPage() {
  if (!REPOSITORY.trim()) {
    return (
      <main className="overview-page">
        <div className="configuration-error" role="alert">
          <h1>Dashboard não configurado</h1>
          <p>Defina <code>VITE_DASHBOARD_REPOSITORY</code> e reinicie o frontend.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="overview-page">
      <header className="overview-header">
        <div className="overview-eyebrow">
          <span className="scan-pulse" aria-hidden="true" />
          {REPOSITORY} · varredura ativa
        </div>
        <div className="overview-title-row">
          <h1>Visão geral de segurança</h1>
          {GATE_MODE === 'advisory' ? <AdvisoryModeBadge /> : null}
        </div>
      </header>
      <div className="widget-grid">
        <Suspense fallback={<SkeletonWidget title="Distribuição por severidade" />}>
          <SeverityDonutWidget repository={REPOSITORY} />
        </Suspense>
        <Suspense fallback={<SkeletonWidget title="Tendência de falhas" />}>
          <WeeklyTrendWidget repository={REPOSITORY} />
        </Suspense>
        <TopCriticalFilesWidget repository={REPOSITORY} />
        <FindingsListWidget repository={REPOSITORY} />
      </div>
    </main>
  );
}

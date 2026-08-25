import { AdvisoryModeBadge } from '../shared/AdvisoryModeBadge';
import { SeverityDonutWidget } from './SeverityDonutWidget';
import { WeeklyTrendWidget } from './WeeklyTrendWidget';
import { TopCriticalFilesWidget } from './TopCriticalFilesWidget';
import { FindingsListWidget } from './FindingsListWidget';

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
  return (
    <main className="overview-page">
      <header className="overview-header">
        <h1>Visão geral de segurança</h1>
        {GATE_MODE === 'advisory' ? <AdvisoryModeBadge /> : null}
      </header>
      <div className="widget-grid">
        <SeverityDonutWidget repository={REPOSITORY} />
        <WeeklyTrendWidget repository={REPOSITORY} />
        <TopCriticalFilesWidget repository={REPOSITORY} />
        <FindingsListWidget repository={REPOSITORY} />
      </div>
    </main>
  );
}

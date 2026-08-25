import type { FindingStatus } from '../../api/dashboard';
import { badgeTextColor, colorTints, typography } from '../../design/tokens';

// Explicit map, one entry per FindingStatus -- never collapsed. In
// particular false_positive and accepted_risk stay two distinct labels:
// they are different reviewer decisions and must read as different.
const LABELS: Record<FindingStatus, string> = {
  open: 'Aberto',
  in_investigation: 'Em investigação',
  resolved: 'Resolvido',
  false_positive: 'Falso positivo',
  accepted_risk: 'Risco aceito',
};

const TINTS: Record<FindingStatus, string> = {
  open: colorTints.high,
  in_investigation: colorTints.medium,
  resolved: colorTints.resolvedAccepted,
  false_positive: colorTints.low,
  accepted_risk: colorTints.resolvedAccepted,
};

export function StatusBadge({ status }: { status: FindingStatus }) {
  return (
    <span
      className="status-badge"
      style={{
        backgroundColor: TINTS[status],
        color: badgeTextColor,
        fontSize: typography.metadata.fontSize,
        letterSpacing: typography.metadata.letterSpacing,
      }}
    >
      {LABELS[status]}
    </span>
  );
}

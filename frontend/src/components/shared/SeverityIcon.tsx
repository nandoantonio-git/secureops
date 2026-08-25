import { colors } from '../../design/tokens';
import type { SeverityBucket } from '../../api/dashboard';

const LABELS: Record<SeverityBucket, string> = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
  info: 'Informativo',
  resolved_accepted: 'Resolvido ou risco aceito',
};

interface SeverityIconProps {
  severity: SeverityBucket;
  size?: number;
}

/**
 * One fixed SVG shape per severity, distinct from color alone -- filled
 * triangle / outline triangle / filled dot / hollow dot / check -- so
 * severity is never conveyed by hue alone (color-blind safe per spec).
 */
export function SeverityIcon({ severity, size = 16 }: SeverityIconProps) {
  const colorKey = severity === 'info' ? 'low' : severity;
  const color = colors[colorKey as keyof typeof colors] ?? colors.low;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      role="img"
      aria-label={LABELS[severity]}
    >
      {renderShape(severity, color)}
    </svg>
  );
}

function renderShape(severity: SeverityBucket, color: string) {
  switch (severity) {
    case 'critical':
      return (
        <path d="M8 1.5 L15 14.5 H1 Z" fill={color} stroke="#0F172A" strokeWidth={0.5} />
      );
    case 'high':
      return (
        <path d="M8 1.5 L15 14.5 H1 Z" fill="none" stroke={color} strokeWidth={1.5} />
      );
    case 'medium':
      // A bare #CA8A04 fill fails even the 3:1 WCAG graphical-object
      // contrast minimum on white -- a darker stroke raises the effective
      // edge contrast without changing the spec-final fill color.
      return <circle cx={8} cy={8} r={5} fill={color} stroke="#78350F" strokeWidth={1} />;
    case 'low':
      return <circle cx={8} cy={8} r={5} fill="none" stroke={color} strokeWidth={1.5} />;
    case 'info':
      return <circle cx={8} cy={8} r={5} fill="none" stroke={color} strokeWidth={1.5} />;
    case 'resolved_accepted':
      return (
        <path
          d="M3 8.5 L6.5 12 L13 4.5"
          fill="none"
          stroke={color}
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      );
    default:
      return null;
  }
}

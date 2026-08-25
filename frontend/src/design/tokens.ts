/**
 * Design tokens for the SecureOps analytics dashboard, matching the
 * "Plano de UI" spec's color/typography/spacing decisions exactly.
 *
 * Accessibility note: the 5 saturated colors below are spec-final, but a
 * manual contrast check against a white background found #EA580C (high) and
 * #16A34A (resolved) pass only the 3:1 WCAG graphical-object minimum (not the
 * 4.5:1 text minimum), and #CA8A04 (medium) fails even the 3:1 graphical
 * minimum (2.80:1). None of the 5 tokens are used as small text color here --
 * only as icon fills/strokes and the large 2rem widget numbers. StatusBadge
 * pairs a light tint with dark text instead of using a saturated color as
 * foreground text, and SeverityIcon's medium dot adds a darker stroke to
 * raise its effective edge contrast.
 */

export const colors = {
  critical: '#DC2626',
  high: '#EA580C',
  medium: '#CA8A04',
  low: '#64748B',
  resolvedAccepted: '#16A34A',
} as const;

/**
 * Brand chrome only (masthead, focus rings, links, controls) -- never used
 * for severity semantics, which stay exclusively on the 5 colors above so
 * "what color means what" never has two answers.
 */
export const brand = {
  ink: '#14171F',
  paper: '#F6F7FB',
  surface: '#FFFFFF',
  line: '#E4E7F0',
  textSecondary: '#565C6D',
  accent: '#2A3EB1',
  accentTint: '#EEF0FC',
} as const;

export const colorTints = {
  critical: '#FEE2E2',
  high: '#FFEDD5',
  medium: '#FEF3C7',
  low: '#F1F5F9',
  resolvedAccepted: '#DCFCE7',
} as const;

export const badgeTextColor = '#1E293B';

export const typography = {
  bigNumber: {
    fontSize: '2rem',
    fontWeight: 600,
    letterSpacing: '-0.02em',
    lineHeight: 1.05,
  },
  widgetTitle: {
    fontSize: '0.875rem',
    fontWeight: 600,
    letterSpacing: '0',
    lineHeight: 1.3,
  },
  tableRow: {
    fontSize: '0.875rem',
    fontWeight: 400,
    letterSpacing: '0',
    lineHeight: 1.5,
  },
  metadata: {
    fontSize: '0.75rem',
    fontWeight: 400,
    letterSpacing: '0.01em',
    lineHeight: 1.4,
  },
  fontFamily: '"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  fontFamilyMono: '"IBM Plex Mono", ui-monospace, Consolas, monospace',
} as const;

export const spacing = {
  widgetGap: '1.5rem',
  widgetPadding: '1.25rem',
} as const;

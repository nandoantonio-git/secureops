import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { getWeeklyTrend } from '../../api/dashboard';
import { usePrefersReducedMotion } from '../../hooks/usePrefersReducedMotion';
import { useWidgetQuery } from '../../hooks/useWidgetQuery';
import { SkeletonWidget } from '../shared/SkeletonWidget';
import { WidgetErrorState } from '../shared/WidgetErrorState';
import { colors } from '../../design/tokens';

const MIN_POINTS_FOR_CHART = 2;

export function WeeklyTrendWidget({ repository }: { repository: string }) {
  const { state, retry } = useWidgetQuery(
    () => getWeeklyTrend(repository),
    [repository],
  );
  const prefersReducedMotion = usePrefersReducedMotion();

  if (state.status === 'loading') {
    return <SkeletonWidget title="Tendência de falhas" />;
  }
  if (state.status === 'error') {
    return <WidgetErrorState widgetName="a tendência de falhas" onRetry={retry} />;
  }

  const { points } = state.data;

  return (
    <div className="widget">
      <h2 className="widget-title">Tendência de falhas</h2>
      {points.length < MIN_POINTS_FOR_CHART ? (
        <p className="widget-empty-state">
          Ainda reunindo histórico. Volte em algumas varreduras.
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <LineChart
            data={points.map((point) => ({
              ...point,
              label: formatWeek(point.week_start),
            }))}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize: 12 }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 12 }} width={28} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="count"
              stroke={colors.high}
              strokeWidth={2}
              dot
              isAnimationActive={!prefersReducedMotion}
              animationDuration={prefersReducedMotion ? 0 : 400}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

function formatWeek(weekStart: string): string {
  const date = new Date(weekStart);
  if (Number.isNaN(date.getTime())) {
    return weekStart;
  }
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
}

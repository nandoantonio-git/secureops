import { Cell, Pie, PieChart, Tooltip } from 'recharts';
import {
  getSeverityDistribution,
  type SeverityBucket,
  type SeverityDistribution,
} from '../../api/dashboard';
import { usePrefersReducedMotion } from '../../hooks/usePrefersReducedMotion';
import { useWidgetQuery } from '../../hooks/useWidgetQuery';
import { SkeletonWidget } from '../shared/SkeletonWidget';
import { WidgetErrorState } from '../shared/WidgetErrorState';
import { colors, typography } from '../../design/tokens';

const BUCKET_COLOR: Record<SeverityBucket, string> = {
  critical: colors.critical,
  high: colors.high,
  medium: colors.medium,
  low: colors.low,
  info: colors.low,
  resolved_accepted: colors.resolvedAccepted,
};

const BUCKET_LABEL: Record<SeverityBucket, string> = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
  info: 'Informativo',
  resolved_accepted: 'Resolvido/Aceito',
};

export function SeverityDonutWidget({ repository }: { repository: string }) {
  const { state, retry } = useWidgetQuery(
    () => getSeverityDistribution(repository),
    [repository],
  );
  const prefersReducedMotion = usePrefersReducedMotion();

  if (state.status === 'loading') {
    return <SkeletonWidget title="Distribuição por severidade" />;
  }
  if (state.status === 'error') {
    return (
      <WidgetErrorState widgetName="a distribuição por severidade" onRetry={retry} />
    );
  }

  return <SeverityDonut data={state.data} prefersReducedMotion={prefersReducedMotion} />;
}

function SeverityDonut({
  data,
  prefersReducedMotion,
}: {
  data: SeverityDistribution;
  prefersReducedMotion: boolean;
}) {
  if (data.total === 0) {
    return (
      <div className="widget">
        <h2 className="widget-title">Distribuição por severidade</h2>
        <p className="widget-empty-state">
          Nenhum finding aberto. Seu código está limpo por enquanto.
        </p>
      </div>
    );
  }

  const chartData = data.segments
    .filter((segment) => segment.count > 0)
    .map((segment) => ({
      bucket: segment.bucket,
      name: BUCKET_LABEL[segment.bucket],
      value: segment.count,
    }));

  return (
    <div className="widget">
      <h2 className="widget-title">Distribuição por severidade</h2>
      <div className="donut-container">
        <PieChart width={196} height={196}>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            innerRadius={58}
            outerRadius={88}
            paddingAngle={2}
            isAnimationActive={!prefersReducedMotion}
            animationDuration={prefersReducedMotion ? 0 : 400}
            animationEasing="ease-out"
          >
            {chartData.map((entry) => (
              <Cell key={entry.bucket} fill={BUCKET_COLOR[entry.bucket]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value, _name, item) => {
              const numericValue = typeof value === 'number' ? value : Number(value);
              const percentage =
                data.total > 0 ? Math.round((numericValue / data.total) * 100) : 0;
              const label =
                (item.payload as { name?: string } | undefined)?.name ?? '';
              return [`${numericValue} (${percentage}%)`, label];
            }}
          />
        </PieChart>
        <div className="donut-center" style={typography.bigNumber}>
          {data.total}
        </div>
      </div>
      <ul className="donut-legend">
        {chartData.map((entry) => (
          <li key={entry.bucket}>
            <span
              className="legend-swatch"
              style={{ backgroundColor: BUCKET_COLOR[entry.bucket] }}
            />
            {entry.name}: {entry.value}
          </li>
        ))}
      </ul>
    </div>
  );
}

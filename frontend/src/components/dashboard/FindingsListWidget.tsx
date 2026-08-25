import { useState } from 'react';
import {
  getFindings,
  overrideFinding,
  type FindingListItem,
  type FindingStatus,
  type Severity,
} from '../../api/dashboard';
import { useWidgetQuery } from '../../hooks/useWidgetQuery';
import { SkeletonWidget } from '../shared/SkeletonWidget';
import { WidgetErrorState } from '../shared/WidgetErrorState';
import { StatusBadge } from '../shared/StatusBadge';
import { SeverityIcon } from '../shared/SeverityIcon';

const PAGE_SIZE = 20;
const DEFAULT_REASON = 'Atualizado a partir do painel.';
const DEFAULT_REVIEWER = 'painel@secureops.local';

const STATUS_OPTIONS: { value: FindingStatus; label: string }[] = [
  { value: 'open', label: 'Aberto' },
  { value: 'in_investigation', label: 'Em investigação' },
  { value: 'resolved', label: 'Resolvido' },
  { value: 'false_positive', label: 'Falso positivo' },
  { value: 'accepted_risk', label: 'Risco aceito' },
];

const SEVERITY_OPTIONS: { value: Severity; label: string }[] = [
  { value: 'critical', label: 'Crítico' },
  { value: 'high', label: 'Alto' },
  { value: 'medium', label: 'Médio' },
  { value: 'low', label: 'Baixo' },
  { value: 'info', label: 'Informativo' },
];

const ALL_FILTER_VALUE = '';

export function FindingsListWidget({ repository }: { repository: string }) {
  const [offset, setOffset] = useState(0);
  const [reviewer, setReviewer] = useState('');
  const [statusFilter, setStatusFilter] = useState<FindingStatus | ''>(
    ALL_FILTER_VALUE,
  );
  const [severityFilter, setSeverityFilter] = useState<Severity | ''>(
    ALL_FILTER_VALUE,
  );
  const { state, retry } = useWidgetQuery(
    () =>
      getFindings({
        repository,
        limit: PAGE_SIZE,
        offset,
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      }),
    [repository, offset, statusFilter, severityFilter],
  );

  function handleStatusFilterChange(value: FindingStatus | '') {
    setStatusFilter(value);
    setOffset(0);
  }

  function handleSeverityFilterChange(value: Severity | '') {
    setSeverityFilter(value);
    setOffset(0);
  }

  if (state.status === 'loading') {
    return <SkeletonWidget title="Lista de falhas detectadas" />;
  }
  if (state.status === 'error') {
    return <WidgetErrorState widgetName="a lista de falhas" onRetry={retry} />;
  }

  const { items, total } = state.data;

  return (
    <div className="widget widget--scrollable">
      <div className="findings-header">
        <h2 className="widget-title">Lista de falhas detectadas</h2>
        <div className="findings-filters">
          <label className="findings-filter">
            Status
            <select
              value={statusFilter}
              onChange={(event) =>
                handleStatusFilterChange(event.target.value as FindingStatus | '')
              }
            >
              <option value={ALL_FILTER_VALUE}>Todos</option>
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="findings-filter">
            Severidade
            <select
              value={severityFilter}
              onChange={(event) =>
                handleSeverityFilterChange(event.target.value as Severity | '')
              }
            >
              <option value={ALL_FILTER_VALUE}>Todas</option>
              {SEVERITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="reviewer-input">
            Revisor
            <input
              type="text"
              value={reviewer}
              onChange={(event) => setReviewer(event.target.value)}
              placeholder="seu-email@empresa.com"
            />
          </label>
        </div>
      </div>
      {items.length === 0 ? (
        <p className="widget-empty-state">
          {statusFilter || severityFilter
            ? 'Nenhum finding corresponde aos filtros selecionados.'
            : 'Nenhum finding aberto. Seu código está limpo por enquanto.'}
        </p>
      ) : (
        <>
          <ul className="findings-list">
            {items.map((item) => (
              <FindingRow
                key={item.id}
                finding={item}
                reviewer={reviewer}
                onChanged={retry}
              />
            ))}
          </ul>
          <div className="findings-pagination">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              Anterior
            </button>
            <span className="findings-pagination-count">
              {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} de {total}
            </span>
            <button
              type="button"
              disabled={offset + PAGE_SIZE >= total}
              onClick={() => setOffset(offset + PAGE_SIZE)}
            >
              Próxima
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function FindingRow({
  finding,
  reviewer,
  onChanged,
}: {
  finding: FindingListItem;
  reviewer: string;
  onChanged: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [nextStatus, setNextStatus] = useState<FindingStatus>(finding.status);
  const [reason, setReason] = useState(DEFAULT_REASON);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (nextStatus === finding.status) {
      setEditing(false);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await overrideFinding(finding.id, {
        changed_by: reviewer.trim() || DEFAULT_REVIEWER,
        change_type: 'status_change',
        to_value: nextStatus,
        reason: reason.trim() || DEFAULT_REASON,
      });
      setEditing(false);
      onChanged();
    } catch {
      setError('Não foi possível salvar. Tente novamente.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <li className="finding-row">
      <SeverityIcon severity={finding.severity} />
      <div className="finding-main">
        <div className="finding-title-line">
          <span className="finding-rule">{finding.rule_id}</span>
          {finding.category ? (
            <span className="finding-category">{finding.category}</span>
          ) : null}
        </div>
        <p className="finding-description">{finding.short_description}</p>
        <span className="finding-location">
          {finding.file_path}:{finding.line_start}
        </span>
      </div>
      <div className="finding-status-control">
        {editing ? (
          // Inline in the row, not a modal/popover -- the spec asks for a
          // low-friction status change, but the override API requires a
          // non-empty reason. Pre-filling it lets a reviewer accept the
          // default with zero extra typing while still supporting a real one.
          <div className="finding-status-editor">
            <select
              value={nextStatus}
              onChange={(event) =>
                setNextStatus(event.target.value as FindingStatus)
              }
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <input
              type="text"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              aria-label="Motivo da mudança"
            />
            <button type="button" onClick={submit} disabled={submitting}>
              Salvar
            </button>
            <button
              type="button"
              onClick={() => setEditing(false)}
              disabled={submitting}
            >
              Cancelar
            </button>
            {error ? <span className="finding-status-error">{error}</span> : null}
          </div>
        ) : (
          <button
            type="button"
            className="status-badge-button"
            onClick={() => setEditing(true)}
          >
            <StatusBadge status={finding.status} />
          </button>
        )}
      </div>
    </li>
  );
}

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getFindings, overrideFinding } from '../../api/dashboard';
import { FindingsListWidget } from './FindingsListWidget';

vi.mock('../../api/dashboard', async (importOriginal) => {
  const original = await importOriginal<typeof import('../../api/dashboard')>();
  return { ...original, getFindings: vi.fn(), overrideFinding: vi.fn() };
});

const mockedGetFindings = vi.mocked(getFindings);
const mockedOverrideFinding = vi.mocked(overrideFinding);
const finding = {
  id: 'finding-1', file_path: 'app/service.py', line_start: 12, line_end: 12,
  rule_id: 'python.command-injection', category: 'Injection',
  severity: 'critical' as const, status: 'open' as const,
  short_description: 'Entrada não confiável alcança um shell.', fingerprint: 'fp-1',
};

describe('FindingsListWidget', () => {
  beforeEach(() => {
    mockedGetFindings.mockResolvedValue({ items: [finding], total: 1, limit: 20, offset: 0 });
    mockedOverrideFinding.mockResolvedValue({});
  });

  it('applies status and severity filters', async () => {
    const user = userEvent.setup();
    render(<FindingsListWidget repository="secureops/service" />);
    await screen.findByText(finding.short_description);
    await user.selectOptions(screen.getByLabelText('Status'), 'open');
    await user.selectOptions(screen.getByLabelText('Severidade'), 'critical');
    await waitFor(() => expect(mockedGetFindings).toHaveBeenLastCalledWith(
      expect.objectContaining({ status: 'open', severity: 'critical', offset: 0 }),
    ));
  });

  it('submits an accessible inline status override', async () => {
    const user = userEvent.setup();
    render(<FindingsListWidget repository="secureops/service" />);
    await user.click(await screen.findByRole('button', { name: `Alterar status de ${finding.rule_id}` }));
    await user.selectOptions(screen.getByLabelText(`Novo status para ${finding.rule_id}`), 'resolved');
    await user.click(screen.getByRole('button', { name: 'Salvar' }));
    await waitFor(() => expect(mockedOverrideFinding).toHaveBeenCalledWith(
      finding.id,
      expect.objectContaining({ change_type: 'status_change', to_value: 'resolved' }),
    ));
  });
});

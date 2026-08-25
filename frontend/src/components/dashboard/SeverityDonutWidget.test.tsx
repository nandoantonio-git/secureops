import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getSeverityDistribution } from '../../api/dashboard';
import { SeverityDonutWidget } from './SeverityDonutWidget';

vi.mock('../../api/dashboard', async (importOriginal) => {
  const original = await importOriginal<typeof import('../../api/dashboard')>();
  return { ...original, getSeverityDistribution: vi.fn() };
});

const mockedGetSeverityDistribution = vi.mocked(getSeverityDistribution);

describe('SeverityDonutWidget', () => {
  beforeEach(() => {
    mockedGetSeverityDistribution.mockReset();
  });

  it('renders the total and per-severity legend', async () => {
    mockedGetSeverityDistribution.mockResolvedValue({
      repository: 'secureops/service',
      total: 3,
      segments: [
        { bucket: 'critical', count: 2 },
        { bucket: 'low', count: 1 },
      ],
    });

    render(<SeverityDonutWidget repository="secureops/service" />);

    expect(await screen.findByText('3')).toBeInTheDocument();
    expect(screen.getByText('Crítico: 2')).toBeInTheDocument();
    expect(screen.getByText('Baixo: 1')).toBeInTheDocument();
  });

  it('shows an empty state when there are no findings', async () => {
    mockedGetSeverityDistribution.mockResolvedValue({
      repository: 'secureops/service',
      total: 0,
      segments: [],
    });

    render(<SeverityDonutWidget repository="secureops/service" />);

    expect(
      await screen.findByText('Nenhum finding aberto. Seu código está limpo por enquanto.'),
    ).toBeInTheDocument();
  });

  it('shows an error state with a working retry', async () => {
    mockedGetSeverityDistribution.mockRejectedValueOnce(new Error('boom'));
    mockedGetSeverityDistribution.mockResolvedValueOnce({
      repository: 'secureops/service',
      total: 1,
      segments: [{ bucket: 'high', count: 1 }],
    });

    const user = userEvent.setup();
    render(<SeverityDonutWidget repository="secureops/service" />);

    await user.click(
      await screen.findByRole('button', { name: 'Tentar de novo' }),
    );

    expect(await screen.findByText('Alto: 1')).toBeInTheDocument();
  });
});

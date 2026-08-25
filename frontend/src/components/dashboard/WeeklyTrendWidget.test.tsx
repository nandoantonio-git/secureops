import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getWeeklyTrend } from '../../api/dashboard';
import { WeeklyTrendWidget } from './WeeklyTrendWidget';

vi.mock('../../api/dashboard', async (importOriginal) => {
  const original = await importOriginal<typeof import('../../api/dashboard')>();
  return { ...original, getWeeklyTrend: vi.fn() };
});

const mockedGetWeeklyTrend = vi.mocked(getWeeklyTrend);

describe('WeeklyTrendWidget', () => {
  beforeEach(() => {
    mockedGetWeeklyTrend.mockReset();
  });

  it('asks the reader to wait when there is not enough history for a chart', async () => {
    mockedGetWeeklyTrend.mockResolvedValue({
      repository: 'secureops/service',
      points: [{ week_start: '2026-08-17', count: 2 }],
    });

    render(<WeeklyTrendWidget repository="secureops/service" />);

    expect(
      await screen.findByText('Ainda reunindo histórico. Volte em algumas varreduras.'),
    ).toBeInTheDocument();
  });

  it('renders the chart once at least two weeks of history exist', async () => {
    mockedGetWeeklyTrend.mockResolvedValue({
      repository: 'secureops/service',
      points: [
        { week_start: '2026-08-10', count: 1 },
        { week_start: '2026-08-17', count: 4 },
      ],
    });

    render(<WeeklyTrendWidget repository="secureops/service" />);

    expect(await screen.findByText('Tendência de falhas')).toBeInTheDocument();
    expect(
      screen.queryByText('Ainda reunindo histórico. Volte em algumas varreduras.'),
    ).not.toBeInTheDocument();
  });

  it('shows an error state on failure', async () => {
    mockedGetWeeklyTrend.mockRejectedValue(new Error('boom'));

    render(<WeeklyTrendWidget repository="secureops/service" />);

    expect(
      await screen.findByText('Não foi possível carregar a tendência de falhas.'),
    ).toBeInTheDocument();
  });
});

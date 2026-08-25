import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getTopCriticalFiles } from '../../api/dashboard';
import { TopCriticalFilesWidget } from './TopCriticalFilesWidget';

vi.mock('../../api/dashboard', async (importOriginal) => {
  const original = await importOriginal<typeof import('../../api/dashboard')>();
  return { ...original, getTopCriticalFiles: vi.fn() };
});

const mockedGetTopCriticalFiles = vi.mocked(getTopCriticalFiles);

describe('TopCriticalFilesWidget', () => {
  beforeEach(() => {
    mockedGetTopCriticalFiles.mockReset();
  });

  it('lists critical files with their finding count', async () => {
    mockedGetTopCriticalFiles.mockResolvedValue({
      repository: 'secureops/service',
      files: [
        { file_path: 'app/routes/invoices.py', count: 3, finding_id: 'f-1', line_start: 42 },
      ],
    });

    render(<TopCriticalFilesWidget repository="secureops/service" />);

    expect(await screen.findByText('app/routes/invoices.py:42')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('shows an empty state when no file has open critical findings', async () => {
    mockedGetTopCriticalFiles.mockResolvedValue({
      repository: 'secureops/service',
      files: [],
    });

    render(<TopCriticalFilesWidget repository="secureops/service" />);

    expect(
      await screen.findByText('Nenhum arquivo com findings críticos abertos.'),
    ).toBeInTheDocument();
  });

  it('shows an error state on failure', async () => {
    mockedGetTopCriticalFiles.mockRejectedValue(new Error('boom'));

    render(<TopCriticalFilesWidget repository="secureops/service" />);

    expect(
      await screen.findByText('Não foi possível carregar os arquivos críticos.'),
    ).toBeInTheDocument();
  });
});

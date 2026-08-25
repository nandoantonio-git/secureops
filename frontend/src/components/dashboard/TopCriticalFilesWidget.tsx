import { getTopCriticalFiles } from '../../api/dashboard';
import { useWidgetQuery } from '../../hooks/useWidgetQuery';
import { SkeletonWidget } from '../shared/SkeletonWidget';
import { WidgetErrorState } from '../shared/WidgetErrorState';
import { truncateMiddle } from '../../utils/truncateMiddle';

const MAX_PATH_CHARS = 40;
const TOP_FILES_LIMIT = 5;

export function TopCriticalFilesWidget({ repository }: { repository: string }) {
  const { state, retry } = useWidgetQuery(
    () => getTopCriticalFiles(repository, TOP_FILES_LIMIT),
    [repository],
  );

  if (state.status === 'loading') {
    return <SkeletonWidget title="Top 5 arquivos críticos" />;
  }
  if (state.status === 'error') {
    return <WidgetErrorState widgetName="os arquivos críticos" onRetry={retry} />;
  }

  const { files } = state.data;

  return (
    <div className="widget">
      <h2 className="widget-title">Top 5 arquivos críticos</h2>
      {files.length === 0 ? (
        <p className="widget-empty-state">
          Nenhum arquivo com findings críticos abertos.
        </p>
      ) : (
        <ol className="top-files-list">
          {files.map((file) => (
            <li key={file.file_path} className="top-files-row">
              <span className="top-files-path" title={file.file_path}>
                {truncateMiddle(file.file_path, MAX_PATH_CHARS)}:{file.line_start}
              </span>
              <span className="top-files-count">{file.count}</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

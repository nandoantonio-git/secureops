/**
 * One widget failing to load must never break the other 3 -- each widget
 * renders its own error state with an independent retry.
 */
export function WidgetErrorState({
  widgetName,
  onRetry,
}: {
  widgetName: string;
  onRetry: () => void;
}) {
  return (
    <div className="widget widget--error" role="alert">
      <p>Não foi possível carregar {widgetName}.</p>
      <button type="button" onClick={onRetry}>
        Tentar de novo
      </button>
    </div>
  );
}

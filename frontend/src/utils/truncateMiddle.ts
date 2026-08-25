/**
 * Truncate the middle of a path, keeping the start and the file name (the
 * end) intact. CSS text-overflow has no middle-ellipsis mode, so this is
 * done in JS with a static maxChars per known column width -- simpler than a
 * ResizeObserver + canvas-measureText dynamic version, sufficient for a
 * fixed-width widget column.
 */
export function truncateMiddle(text: string, maxChars: number): string {
  if (text.length <= maxChars) {
    return text;
  }
  if (maxChars <= 1) {
    return text.slice(0, Math.max(maxChars, 0));
  }

  const ellipsis = '…';
  const remaining = maxChars - ellipsis.length;
  const headLength = Math.ceil(remaining / 2);
  const tailLength = Math.floor(remaining / 2);

  const head = text.slice(0, headLength);
  const tail = tailLength > 0 ? text.slice(text.length - tailLength) : '';
  return `${head}${ellipsis}${tail}`;
}

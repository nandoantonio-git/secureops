const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  'http://localhost:8000';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type QueryParams = Record<string, string | number | boolean | undefined>;

function buildUrl(path: string, params: QueryParams): string {
  const url = new URL(path, API_BASE_URL);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

export async function apiGet<T>(
  path: string,
  params: QueryParams = {},
): Promise<T> {
  const response = await fetch(buildUrl(path, params));
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `GET ${path} failed with status ${response.status}`,
    );
  }
  return (await response.json()) as T;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(buildUrl(path, {}), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `POST ${path} failed with status ${response.status}`,
    );
  }
  return (await response.json()) as T;
}

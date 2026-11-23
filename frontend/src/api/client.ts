export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
    retryable: boolean;
    details: Record<string, any>;
    request_id: string;
  };
}

export class ApiError extends Error {
  code: string;
  retryable: boolean;
  details: Record<string, any>;
  requestId: string;
  statusCode: number;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.error?.message || `HTTP ${status}`);
    this.name = 'ApiError';
    this.statusCode = status;
    this.code = payload.error?.code || 'UNKNOWN_ERROR';
    this.retryable = payload.error?.retryable || false;
    this.details = payload.error?.details || {};
    this.requestId = payload.error?.request_id || '';
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = path.startsWith('/') ? path : `/api/v1/${path}`;
  const headers = new Headers(options.headers || {});

  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }

  // Don't set Content-Type for FormData (browser sets boundary automatically)
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let payload: ApiErrorPayload;
    try {
      payload = await response.json();
    } catch {
      payload = {
        error: {
          code: `HTTP_${response.status}`,
          message: response.statusText || 'An error occurred',
          retryable: response.status >= 500,
          details: {},
          request_id: response.headers.get('X-Request-ID') || '',
        },
      };
    }
    throw new ApiError(response.status, payload);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

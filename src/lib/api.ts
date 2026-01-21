export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown;
};

async function request<T>(url: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options;

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...headers
    },
    body: body ? JSON.stringify(body) : undefined,
    ...rest
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(response.status, response.statusText, data);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  get<T>(url: string, options?: RequestOptions): Promise<T> {
    return request<T>(url, { ...options, method: 'GET' });
  },

  post<T>(url: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(url, { ...options, method: 'POST', body });
  },

  put<T>(url: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(url, { ...options, method: 'PUT', body });
  },

  patch<T>(url: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(url, { ...options, method: 'PATCH', body });
  },

  delete<T>(url: string, options?: RequestOptions): Promise<T> {
    return request<T>(url, { ...options, method: 'DELETE' });
  }
};

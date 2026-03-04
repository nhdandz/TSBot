interface RequestOptions {
  headers?: Record<string, string>
}

class ApiClient {
  private authToken: string | null = null

  constructor() {
    this.authToken = localStorage.getItem('auth_token')
  }

  setAuthToken(token: string) {
    this.authToken = token
  }

  clearAuthToken() {
    this.authToken = null
    localStorage.removeItem('auth_token')
  }

  private async request<T>(
    method: string,
    url: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const headers: Record<string, string> = {
      ...options?.headers,
    }

    const isFormData = body instanceof FormData
    if (!isFormData) {
      headers['Content-Type'] = 'application/json'
    }

    const response = await fetch(url, {
      method,
      headers,
      body: body
        ? isFormData
          ? (body as FormData)
          : JSON.stringify(body)
        : undefined,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  get<T>(url: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('GET', url, undefined, options)
  }

  post<T>(url: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('POST', url, body, options)
  }

  put<T>(url: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>('PUT', url, body, options)
  }

  delete<T = { success: boolean }>(url: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('DELETE', url, undefined, options)
  }
}

export const apiClient = new ApiClient()

export function withAuth(): Record<string, string> {
  const token = localStorage.getItem('auth_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

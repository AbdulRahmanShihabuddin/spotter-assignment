import { RoutePlanRequest, RoutePlanResponse, ApiErrorResponse } from '../types/route';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export class ApiError extends Error {
  detail?: string;
  code?: string;
  statusCode: number;

  constructor(message: string, statusCode: number, detail?: string, code?: string) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.detail = detail;
    this.code = code;
  }
}

export async function planRoute(request: RoutePlanRequest): Promise<RoutePlanResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/routes/plan/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Network communication failed';
    throw new ApiError(
      'Unable to connect to the routing server. Please check your network or ensure the backend service is running.',
      0,
      message,
      'network_error'
    );
  }

  if (!response.ok) {
    let errorData: ApiErrorResponse | null = null;
    try {
      errorData = await response.json();
    } catch {
      // Non-JSON response
    }

    if (errorData) {
      // Check field-level details
      if (errorData.details) {
        const firstField = Object.keys(errorData.details)[0];
        const fieldError = Array.isArray(errorData.details[firstField])
          ? errorData.details[firstField][0]
          : errorData.details[firstField];
        throw new ApiError(
          `${firstField}: ${fieldError}`,
          response.status,
          errorData.detail,
          errorData.code
        );
      }

      throw new ApiError(
        errorData.detail || errorData.error || 'Route planning request failed.',
        response.status,
        errorData.detail,
        errorData.code
      );
    }

    throw new ApiError(
      `Routing server returned status ${response.status} (${response.statusText}).`,
      response.status
    );
  }

  return response.json();
}

export async function checkBackendHealth(): Promise<{ status: string; routing_provider: string; is_mock: boolean }> {
  try {
    const res = await fetch(`${API_BASE_URL}/health/`);
    if (res.ok) {
      return res.json();
    }
  } catch {
    // Health check failed
  }
  return { status: 'offline', routing_provider: 'unavailable', is_mock: false };
}

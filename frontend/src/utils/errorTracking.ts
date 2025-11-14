/**
 * Error tracking and logging utilities.
 *
 * Provides type-safe error handling and logging.
 * In production, integrate with services like Sentry, LogRocket, etc.
 */

export interface ApiError {
  message: string;
  status?: number;
  statusText?: string;
  details?: Record<string, unknown>;
}

/**
 * Extract error message from unknown error type.
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  if (error && typeof error === 'object') {
    if ('message' in error && typeof error.message === 'string') {
      return error.message;
    }
    if ('detail' in error && typeof error.detail === 'string') {
      return error.detail;
    }
  }

  return 'An unexpected error occurred';
}

/**
 * Log error for debugging/monitoring.
 * In production, sends to error tracking service.
 */
export function logError(message: string, context?: Record<string, unknown>): void {
  if (process.env.NODE_ENV === 'production') {
    // TODO: Integrate with error tracking service
    // Sentry.captureException(new Error(message), { extra: context });
  } else {
    console.error(`[Error] ${message}`, context);
  }
}

/**
 * Log warning for debugging.
 */
export function logWarning(message: string, context?: Record<string, unknown>): void {
  if (process.env.NODE_ENV === 'development') {
    console.warn(`[Warning] ${message}`, context);
  }
}

/**
 * Parse API error response.
 */
export function parseApiError(error: unknown): ApiError {
  if (error && typeof error === 'object') {
    const err = error as Record<string, unknown>;

    return {
      message: getErrorMessage(error),
      status: typeof err.status === 'number' ? err.status : undefined,
      statusText: typeof err.statusText === 'string' ? err.statusText : undefined,
      details: err.details as Record<string, unknown> | undefined,
    };
  }

  return {
    message: getErrorMessage(error),
  };
}

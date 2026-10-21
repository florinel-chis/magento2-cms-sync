import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Shape of a FastAPI validation error entry (HTTP 422)
interface ValidationErrorEntry {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
}

interface ErrorResponseBody {
  detail?: unknown;
  message?: unknown;
}

const isValidationErrorEntry = (value: unknown): value is ValidationErrorEntry =>
  typeof value === 'object' && value !== null && ('msg' in value || 'loc' in value);

// Turn whatever the backend put in the response body into a readable message
const extractErrorMessage = (data: unknown): string => {
  if (typeof data === 'object' && data !== null) {
    const body = data as ErrorResponseBody;
    const detail = body.detail;

    if (typeof detail === 'string' && detail) {
      return detail;
    }

    if (Array.isArray(detail)) {
      // FastAPI 422: [{loc: [...], msg: "...", type: "..."}]
      const parts = detail.map((entry: unknown) => {
        if (isValidationErrorEntry(entry)) {
          const loc = Array.isArray(entry.loc) ? entry.loc.join('.') : '';
          const msg = entry.msg ?? JSON.stringify(entry);
          return loc ? `${loc}: ${msg}` : msg;
        }
        return typeof entry === 'string' ? entry : JSON.stringify(entry);
      });
      if (parts.length > 0) {
        return parts.join('; ');
      }
    }

    if (typeof detail === 'object' && detail !== null) {
      return JSON.stringify(detail);
    }

    if (typeof body.message === 'string' && body.message) {
      return body.message;
    }
  }

  return 'An error occurred';
};

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      return Promise.reject(new Error(extractErrorMessage(error.response.data)));
    } else if (error.request) {
      // Request was made but no response received
      return Promise.reject(new Error('Network error. Please check your connection.'));
    } else {
      // Something else happened
      return Promise.reject(new Error('An unexpected error occurred'));
    }
  }
);

export default api;

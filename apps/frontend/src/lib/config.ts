const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const config = {
  apiBaseUrl: API_BASE_URL,
  environment: import.meta.env.VITE_ENVIRONMENT || "development",
} as const;

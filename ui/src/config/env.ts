export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const

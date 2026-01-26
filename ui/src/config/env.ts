export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  allauthBaseUrl:
    import.meta.env.VITE_ALLAUTH_BASE_URL || '/_allauth/browser/v1',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const

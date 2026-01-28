export const env = {
  // 注意：API SDK 的 URL 已包含 /api 前綴（如 /api/comics/series/）
  // 所以 baseUrl 應為空字串（本地）或不含 /api 的網域（生產）
  // 使用 ?? 而非 ||：允許明確設置空字串作為有效值
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  // 使用 ||：空字串應回退到預設值，因為 allauth 需要有效路徑
  allauthBaseUrl:
    import.meta.env.VITE_ALLAUTH_BASE_URL || '/_allauth/browser/v1',
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const

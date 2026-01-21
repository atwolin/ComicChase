/**
 * API Client - 統一導出入口
 *
 * 此文件整合自動生成的 API Client (@hey-api/openapi-ts)
 * 並提供統一的導入路徑
 */

import { client } from './generated/client.gen'
import { env } from '@/config/env'
import { getCSRFToken } from '@/lib/django'

// ============================================================
// 配置 API Client
// ============================================================

// 創建自定義 fetch 函數，自動添加 credentials
// 這樣所有請求都會包含 cookies (session, CSRF token 等)
const customFetch: typeof fetch = (input, init) => {
  // 確保 init 存在
  const requestInit = init || {}

  // 設置 credentials: 'include' 來發送跨域 cookies
  return globalThis.fetch(input, {
    ...requestInit,
    credentials: 'include',
  })
}

// 配置 baseURL 和自定義 fetch（使用環境變數或默認為 '/api'）
// 在生產環境中，VITE_API_BASE_URL 應該是完整的後端 URL
// 例如: https://comicchase-service-664556590362.us-central1.run.app/api
client.setConfig({
  baseUrl: env.apiBaseUrl,
  fetch: customFetch,
})

// ============================================================
// Request Interceptor - 添加 CSRF Token
// ============================================================

client.interceptors.request.use((request, _options) => {
  // 添加 CSRF Token header（Django 要求）
  const csrfToken = getCSRFToken()
  if (csrfToken) {
    request.headers.set('X-CSRFToken', csrfToken)
  }

  return request
})

// ============================================================
// 導出所有 API 函數和類型
// ============================================================

// 導出所有 API 函數（如 comicsSeriesList, comicsSeriesRetrieve 等）
export * from './generated/sdk.gen'

// 導出所有 TypeScript 類型
export * from './generated/types.gen'

// 導出 client 實例（供需要直接操作 client 的場景使用）
export { client }

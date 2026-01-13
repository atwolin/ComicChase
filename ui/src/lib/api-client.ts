/**
 * API Client 配置
 * 配置請求攔截器自動添加 CSRF Token
 */

import { client } from '@/api/generated/client.gen'
import { getCSRFToken } from './django'

// 配置請求攔截器，自動添加 CSRF Token
client.interceptors.request.use((request, options) => {
  // 對於需要 CSRF 保護的請求方法
  const method = options.method?.toLowerCase()
  if (method && ['post', 'put', 'patch', 'delete'].includes(method)) {
    const csrfToken = getCSRFToken()
    if (csrfToken) {
      request.headers.set('X-CSRFToken', csrfToken)
    }
  }

  return request
})

// 配置錯誤攔截器
client.interceptors.error.use(error => {
  // 處理 403 CSRF 錯誤
  if (error instanceof Response && error.status === 403) {
    console.error('[API] CSRF 錯誤 403 Forbidden')
  }
  return error
})

export { client }

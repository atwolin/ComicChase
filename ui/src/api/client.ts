import axios, { AxiosError } from 'axios'
import { queryClient } from '@/lib/react-query'
import type { Series, SeriesListParams, SeriesListResponse } from '@/types'
import { env } from '@/config/env'
import { getCSRFToken } from '@/lib/django'

const apiClient = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: 15 * 1000, // 15 seconds
  headers: {
    'Content-Type': 'application/json',
  },
  // CRITICAL: 啟用 withCredentials 以支持跨子網域 cookies
  // Frontend (comicchase.site) 和 Backend (api.comicchase.site) 共用 .comicchase.site cookies
  withCredentials: true,
})

// Request Interceptor（請求攔截器）- 添加 CSRF Token
apiClient.interceptors.request.use(
  config => {
    // 為所有請求添加 CSRF Token（Django 要求）
    const csrfToken = getCSRFToken()
    if (csrfToken && config.headers) {
      config.headers['X-CSRFToken'] = csrfToken
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response Interceptor（回應攔截器）
apiClient.interceptors.response.use(
  response => response,
  (error: AxiosError) => {
    // 詳細的錯誤日誌
    const url = error.config?.url || 'unknown'
    const status = error.response?.status

    if (env.isDevelopment) {
      console.error('[API Client] 錯誤攔截器觸發:', {
        url,
        status,
        message: error.message,
        config: error.config,
        response: error.response,
      })
    }

    // 統一錯誤處理
    if (error.response?.status === 401) {
      console.error('[API Client] 偵測到 401 未授權錯誤')

      // CRITICAL FIX: 不要因為 allauth session 檢查的正常 401 錯誤而清除快取
      // allauth 的 session 端點在未登入時回傳 401 是正常行為
      const isAllauthSessionCheck = url.includes(
        '/_allauth/browser/v1/auth/session'
      )
      const isAllauthConfigCheck = url.includes('/_allauth/browser/v1/config')

      if (isAllauthSessionCheck || isAllauthConfigCheck) {
        console.log(
          '[API Client] 這是 allauth 認證檢查的正常 401，不清除快取或重定向'
        )
        return Promise.reject(error)
      }

      // 其他 API 的 401 錯誤才清除快取並重新導向
      console.error(
        '[API Client] 非 allauth 的 401 錯誤，清除快取並重定向到登入頁'
      )
      queryClient.clear()
      // TODO: Update url after implementing login page
      window.location.href = '/login'
    } else if (error.response?.status === 500) {
      // 伺服器錯誤，可以送到錯誤追蹤服務（如 Sentry）
      console.error('[API Client] Server error:', error)
    }

    return Promise.reject(error)
  }
)

export const seriesApi = {
  /**
   * 獲取漫畫系列列表
   */
  getSeriesList: async (
    params?: SeriesListParams
  ): Promise<SeriesListResponse> => {
    const response = await apiClient.get<SeriesListResponse>(
      '/comics/series/',
      {
        params,
      }
    )
    return response.data
  },

  /**
   * 獲取漫畫系列詳情
   */
  getSeriesDetail: async (id: number): Promise<Series> => {
    const response = await apiClient.get<Series>(`/comics/series/${id}/`)
    return response.data
  },
}

export default apiClient

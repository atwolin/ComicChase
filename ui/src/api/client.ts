import axios, { AxiosError } from 'axios'
import { queryClient } from '@/lib/react-query'
import type { Series, SeriesListParams, SeriesListResponse } from '@/types'
import { env } from '@/config/env'

const apiClient = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: 15 * 1000, // 15 seconds
  headers: {
    'Content-Type': 'application/json',
  },
})

// Response Interceptor（回應攔截器）
apiClient.interceptors.response.use(
  response => response,
  (error: AxiosError) => {
    // 統一錯誤處理
    if (error.response?.status === 401) {
      // 未授權，清除快取並重新導向
      queryClient.clear()
      // TODO: Update url after implementing login page
      window.location.href = '/login'
    } else if (error.response?.status === 500) {
      // 伺服器錯誤，可以送到錯誤追蹤服務（如 Sentry）
      console.error('Server error:', error)
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

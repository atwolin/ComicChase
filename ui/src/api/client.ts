import axios from 'axios'
import type { Series, SeriesListParams, SeriesListResponse } from '@/types'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const seriesApi = {
  /**
   * 獲取漫畫系列列表
   */
  getSeriesList: async (params?: SeriesListParams): Promise<SeriesListResponse> => {
    const response = await apiClient.get<SeriesListResponse>('/series/', { params })
    return response.data
  },

  /**
   * 獲取漫畫系列詳情
   */
  getSeriesDetail: async (id: number): Promise<Series> => {
    const response = await apiClient.get<Series>(`/series/${id}/`)
    return response.data
  },
}

export default apiClient

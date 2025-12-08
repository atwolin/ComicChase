import axios from 'axios'
import type {
  Series,
  SeriesListParams,
  SeriesListResponse,
  User,
  UserCollection,
  LoginResponse,
  RegisterData,
  LoginData,
} from '@/types'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// 添加請求攔截器以附加授權
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 添加響應攔截器以處理 401 錯誤並嘗試刷新
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post('/api/auth/refresh/', {
            refresh: refreshToken,
          })
          const { access } = response.data
          localStorage.setItem('access_token', access)
          originalRequest.headers.Authorization = `Bearer ${access}`
          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

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

export const authApi = {
  /**
   * 使用者註冊
   */
  register: async (data: RegisterData): Promise<{ message: string; user: User }> => {
    const response = await apiClient.post('/auth/register/', data)
    return response.data
  },

  /**
   * 使用者登錄
   */
  login: async (data: LoginData): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login/', data)
    const { access, refresh } = response.data
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    return response.data
  },

  /**
   * 獲取目前使用者資訊
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me/')
    return response.data
  },

  /**
   * 登出
   */
  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  /**
   * 檢查是否已登錄
   */
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('access_token')
  },
}

export const collectionApi = {
  /**
   * 獲取使用者收藏列表
   */
  getCollections: async (): Promise<{ results: UserCollection[] }> => {
    const response = await apiClient.get<{ results: UserCollection[] }>('/collections/')
    return response.data
  },

  /**
   * 添加收藏
   */
  addCollection: async (seriesId: number): Promise<UserCollection> => {
    const response = await apiClient.post<UserCollection>('/collections/', {
      series_id: seriesId,
    })
    return response.data
  },

  /**
   * 刪除收藏
   */
  removeCollection: async (id: number): Promise<void> => {
    await apiClient.delete(`/collections/${id}/`)
  },
}

export default apiClient

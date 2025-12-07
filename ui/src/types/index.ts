export interface Publisher {
  id: number
  name: string
  region: 'JP' | 'TW'
}

export interface Volume {
  id: number
  volume_number: number | null
  region: 'JP' | 'TW'
  variant: string
  release_date: string | null
  isbn: string | null
  publisher: number | null
  publisher_name: string | null
}

export interface Series {
  id: number
  traditional_chinese_title: string | null
  japanese_title: string
  author: string
  status_japan: 'ongoing' | 'completed' | 'hiatus'
  genres?: string[]
  first_published_year?: number | null
  latest_volume_jp_number?: number | null
  latest_volume_tw_number?: number | null
  volumes?: Volume[]
}

export interface SeriesListResponse {
  count: number
  next: string | null
  previous: string | null
  results: Series[]
}

export interface SeriesListParams {
  search?: string
  ordering?: string
  page?: number
  page_size?: number
  status_jp?: 'ongoing' | 'completed' | 'hiatus'
  genre?: string
  year?: number | string
}

// 用戶資料
export interface User {
  id: number
  username: string
  email: string
  date_joined: string
}

// 用戶收藏的漫畫系列
export interface UserCollection {
  id: number
  series: Series
  series_id?: number
  created_at: string
  notes?: string
}

export interface LoginData {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  password: string
  email?: string
}

export interface LoginResponse {
  access: string
  refresh: string
}

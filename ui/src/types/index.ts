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
  image_url: string | null
  publisher: number | null
  publisher_name: string | null
}

export interface Series {
  id: number
  title_tw: string
  title_jp: string
  author_tw: string
  author_jp: string
  author: string // 計算欄位：整合的作者名稱
  status_jp: 'ongoing' | 'completed' | 'hiatus'
  genres?: string[]
  first_published_year?: number | null
  latest_volume_jp_number?: number | null
  latest_volume_tw_number?: number | null
  latest_volume_jp_image?: string | null
  latest_volume_tw_image?: string | null
  volumes?: Volume[]
  cover_image?: string | null
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

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

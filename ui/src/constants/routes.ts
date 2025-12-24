export const ROUTES = {
  HOME: '/',
  SERIES_LIST: '/comics/series',
  SERIES_DETAIL: (id: number | string) => `/comics/series/${id}`,
  SERIES_DETAIL_PATTERN: '/comics/series/:id',
} as const

export const buildSeriesSearchUrl = (searchQuery: string) => {
  return `/series?search=${encodeURIComponent(searchQuery.trim())}`
}

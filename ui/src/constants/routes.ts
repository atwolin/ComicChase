export const ROUTES = {
  HOME: '/',
  SERIES_LIST: '/series',
  SERIES_DETAIL: (id: number | string) => `/comics/series/${id}`,
} as const

export const buildSeriesSearchUrl = (searchQuery: string) => {
  return `/series?search=${encodeURIComponent(searchQuery.trim())}`
}

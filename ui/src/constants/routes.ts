export const ROUTES = {
  HOME: '/',
  SERIES_LIST: '/comics/series/',
  SERIES_DETAIL: (id: number | string) => `/comics/series/${id}/`,
  SERIES_DETAIL_PATTERN: '/comics/series/:id',
  LOGIN: '/login',
  SIGNUP: '/signup',
  MY_SUBSCRIPTIONS: '/my-subscriptions',
} as const

export const buildSeriesSearchUrl = (searchQuery: string) => {
  return `${ROUTES.SERIES_LIST}?search=${encodeURIComponent(searchQuery.trim())}`
}

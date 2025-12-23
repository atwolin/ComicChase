import type { SeriesListParams } from '@/types'

export const seriesKeys = {
  all: ['series'] as const,
  lists: () => [...seriesKeys.all, 'list'] as const,
  list: (params?: SeriesListParams) => [...seriesKeys.lists(), params] as const,
  details: () => [...seriesKeys.all, 'detail'] as const,
  detail: (id: number) => [...seriesKeys.details(), id] as const,
}

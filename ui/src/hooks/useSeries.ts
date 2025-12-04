import { useQuery } from '@tanstack/react-query'
import { seriesApi } from '@/api/client'
import type { SeriesListParams } from '@/types'

export const useSeriesList = (params?: SeriesListParams) => {
  return useQuery({
    queryKey: ['series', 'list', params],
    queryFn: () => seriesApi.getSeriesList(params),
  })
}

export const useSeriesDetail = (id: number) => {
  return useQuery({
    queryKey: ['series', 'detail', id],
    queryFn: () => seriesApi.getSeriesDetail(id),
    enabled: !!id,
  })
}



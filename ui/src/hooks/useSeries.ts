import { useQuery } from '@tanstack/react-query'
import { seriesApi } from '@/api/client'
import type { Series, SeriesListParams, SeriesListResponse } from '@/types'
import { seriesKeys } from '@/constants/queryKeys'

// 詳細漫畫資料的回應型別
type SeriesDetailResponse = Series

export const useSeriesList = (params?: SeriesListParams) => {
  return useQuery<SeriesListResponse>({
    queryKey: seriesKeys.list(params),
    queryFn: () => seriesApi.getSeriesList(params),
  })
}

// 取得單一漫畫詳細資料的 Hook
export const useSeriesDetail = (id: number | undefined) => {
  return useQuery<SeriesDetailResponse>({
    queryKey: seriesKeys.detail(id!),
    queryFn: () => seriesApi.getSeriesDetail(id!),
    enabled: !!id,
  })
}

/**
 * Series Query Hooks
 *
 * 使用自動生成的 API (@hey-api/openapi-ts) 與 React Query 整合
 */

import { useQuery } from '@tanstack/react-query'
import { comicsSeriesList, comicsSeriesRetrieve } from '@/api'
import type {
  ComicsSeriesListData,
  PaginatedSeriesListList,
  SeriesDetail,
} from '@/api'
import { seriesKeys } from '@/constants/queryKeys'

// ============================================================
// 1. 漫畫列表查詢 Hook
// ============================================================

// 定義查詢參數類型（基於自動生成的類型）
export type UseSeriesListParams = ComicsSeriesListData['query']

/**
 * 查詢漫畫系列列表
 * @param params - 查詢參數（search, ordering, page, page_size）
 * @returns React Query 查詢結果
 */
export const useSeriesList = (params?: UseSeriesListParams) => {
  return useQuery<PaginatedSeriesListList>({
    queryKey: seriesKeys.list(params),
    queryFn: async () => {
      console.log('[useSeriesList] 開始請求漫畫列表，參數:', params)
      try {
        const { data } = await comicsSeriesList({
          query: params,
        })
        console.log('[useSeriesList] 漫畫列表請求成功，資料:', data)
        return data!
      } catch (error) {
        console.error('[useSeriesList] 漫畫列表請求失敗:', error)
        throw error
      }
    },
  })
}

// ============================================================
// 2. 漫畫詳情查詢 Hook
// ============================================================

/**
 * 查詢單一漫畫詳情
 * @param id - 漫畫系列 ID
 * @returns React Query 查詢結果
 */
export const useSeriesDetail = (id: number | undefined) => {
  return useQuery<SeriesDetail>({
    queryKey: seriesKeys.detail(id!),
    queryFn: async () => {
      if (!id) {
        throw new Error('Series ID is required')
      }
      const { data } = await comicsSeriesRetrieve({
        path: { id },
      })
      return data!
    },
    enabled: !!id, // 只在有 ID 時執行查詢
  })
}

/**
 * 訂閱管理 Hooks
 *
 * 管理使用者追蹤漫畫系列的功能
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  subscriptionsList,
  subscriptionsCreate,
  subscriptionsBySeriesDestroy,
  type SubscriptionsListData,
} from '@/api'

// ============================================================
// Query Keys
// ============================================================

export const subscriptionKeys = {
  all: ['subscriptions'] as const,
  lists: () => [...subscriptionKeys.all, 'list'] as const,
  list: (params?: SubscriptionsListData['query']) =>
    [...subscriptionKeys.lists(), params] as const,
}

// ============================================================
// 查詢 Hooks
// ============================================================

/**
 * 獲取使用者的所有訂閱
 */
export function useSubscriptions(
  params?: SubscriptionsListData['query'],
  enabled = true
) {
  return useQuery({
    queryKey: subscriptionKeys.list(params),
    queryFn: async () => {
      console.log('[useSubscriptions] 正在獲取訂閱列表...')
      const { data } = await subscriptionsList({ query: params })
      console.log('[useSubscriptions] 訂閱列表:', data)
      return data!
    },
    enabled, // 只在啟用時查詢
  })
}

/**
 * 檢查是否已追蹤某個系列
 */
export function useIsSubscribed(seriesId: number, enabled = true) {
  const { data } = useSubscriptions(undefined, enabled)

  // 檢查訂閱列表中是否有該系列
  const isSubscribed =
    data?.results?.some(sub => sub.series === seriesId) || false

  console.log(
    `[useIsSubscribed] Series ${seriesId}:`,
    isSubscribed,
    'Total subscriptions:',
    data?.results?.length || 0
  )

  return isSubscribed
}

// ============================================================
// Mutation Hooks
// ============================================================

/**
 * 追蹤系列
 */
export function useSubscribe() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (seriesId: number) => {
      const { data } = await subscriptionsCreate({
        body: {
          series: seriesId,
          receive_email: true, // 預設啟用 email 通知
          receive_line: false, // 預設不啟用 Line 通知
        },
      })
      return data!
    },
    onSuccess: () => {
      // 重新獲取訂閱列表
      queryClient.invalidateQueries({
        queryKey: subscriptionKeys.lists(),
      })
    },
  })
}

/**
 * 取消追蹤系列
 */
export function useUnsubscribe() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (seriesId: number) => {
      await subscriptionsBySeriesDestroy({
        path: { series_id: seriesId.toString() },
      })
    },
    onSuccess: () => {
      // 重新獲取訂閱列表
      queryClient.invalidateQueries({
        queryKey: subscriptionKeys.lists(),
      })
    },
  })
}

/**
 * 切換追蹤狀態（追蹤/取消）
 */
export function useToggleSubscription(seriesId: number, enabled = true) {
  const isSubscribed = useIsSubscribed(seriesId, enabled)
  const subscribe = useSubscribe()
  const unsubscribe = useUnsubscribe()

  const toggle = async () => {
    console.log(
      '[useToggleSubscription] 開始切換, seriesId:',
      seriesId,
      'isSubscribed:',
      isSubscribed
    )

    if (isSubscribed) {
      console.log('[useToggleSubscription] 取消追蹤...')
      await unsubscribe.mutateAsync(seriesId)
    } else {
      console.log('[useToggleSubscription] 追蹤系列...')
      await subscribe.mutateAsync(seriesId)
    }

    console.log('[useToggleSubscription] 切換完成')
  }

  return {
    isSubscribed,
    toggle,
    isLoading: subscribe.isPending || unsubscribe.isPending,
    error: subscribe.error || unsubscribe.error,
  }
}

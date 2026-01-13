import { Link } from 'react-router-dom'
import { useEffect } from 'react'
import { useQueries } from '@tanstack/react-query'
import { useSubscriptions } from '@/hooks/useSubscription'
import { useRequireAuth } from '@/hooks/useRequireAuth'
import { SeriesCard } from '@/components/SeriesCard'
import { Loading } from '@/components/Loading'
import { ErrorDisplay } from '@/components/Error'
import { ROUTES } from '@/constants/routes'
import { comicsSeriesRetrieve } from '@/api'

/**
 * 我的追蹤頁面
 * 顯示使用者追蹤的所有漫畫系列
 * 需要登入才能訪問
 */
export const MySubscriptions = () => {
  // 認證檢查
  const { isAuthenticated, navigateToLogin } = useRequireAuth()

  const { data, isLoading, isError, refetch } = useSubscriptions(
    undefined,
    isAuthenticated
  )

  const subscriptions = data?.results || []
  const hasSubscriptions = subscriptions.length > 0

  // 使用 useQueries 批量查詢每個系列的詳情
  // 注意：必須在所有 early returns 之前調用（React Hooks 規則）
  const seriesQueries = useQueries({
    queries: hasSubscriptions
      ? subscriptions.map(subscription => ({
          queryKey: ['series', subscription.series],
          queryFn: async () => {
            const { data } = await comicsSeriesRetrieve({
              path: { id: subscription.series },
            })
            // 返回原始數據，讓下游過濾處理 undefined
            return data
          },
        }))
      : [], // 如果沒有訂閱，返回空陣列
  })

  // 未登入自動導向登入頁（使用 useEffect 避免渲染期間的副作用）
  useEffect(() => {
    if (!isAuthenticated) {
      navigateToLogin()
    }
  }, [isAuthenticated, navigateToLogin])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <Loading />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <ErrorDisplay
          message="無法載入追蹤列表，請檢查網路連線"
          onRetry={refetch}
        />
      </div>
    )
  }

  // 檢查是否所有系列都載入完成
  const isLoadingSeries = seriesQueries.some(query => query.isLoading)

  // 將 SeriesDetail 轉換為 SeriesList 格式，並過濾掉 undefined
  const seriesData = seriesQueries
    .map(query => query.data)
    .filter(
      (data): data is NonNullable<typeof data> =>
        data !== undefined && data !== null
    )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative container mx-auto px-4 py-16">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            我的追蹤
          </h1>
          <p className="text-white/90 text-lg">
            追蹤 {subscriptions.length} 部漫畫
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8">
        {hasSubscriptions ? (
          <>
            <div className="mb-6 flex items-center justify-between">
              <p className="text-gray-600">
                共 {subscriptions.length} 部追蹤中的漫畫
              </p>
            </div>

            {isLoadingSeries ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                <p className="ml-4 text-gray-600">載入漫畫資訊中...</p>
              </div>
            ) : (
              /* 漫畫列表 - 使用 SeriesCard */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {seriesData.map(series => (
                  <SeriesCard key={series.id} series={series} />
                ))}
              </div>
            )}
          </>
        ) : (
          /* 空狀態 */
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
            <div className="mb-6">
              <svg
                className="mx-auto h-24 w-24 text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              還沒有追蹤任何漫畫
            </h2>
            <p className="text-gray-600 mb-8">
              開始追蹤您喜愛的漫畫，隨時掌握最新出版資訊
            </p>
            <Link
              to={ROUTES.SERIES_LIST}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              瀏覽漫畫
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

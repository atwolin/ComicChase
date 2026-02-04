import { Link, useSearchParams } from 'react-router-dom'
import { useEffect } from 'react'
import { useQueries } from '@tanstack/react-query'
import { useSubscriptions } from '@/hooks/useSubscription'
import { useUserPreferences } from '@/hooks/useUserPreferences'
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

  // 分頁狀態
  const [searchParams, setSearchParams] = useSearchParams()
  const currentPage = Number(searchParams.get('page')) || 1

  const { data, isLoading, isError, refetch } = useSubscriptions(
    { page: currentPage },
    isAuthenticated
  )

  // 分頁資訊
  const paginatedData = !Array.isArray(data) ? data : null
  const subscriptions = Array.isArray(data) ? data : data?.results || []
  const totalCount = paginatedData?.count || subscriptions.length
  const pageSize = 12 // 與後端 PAGE_SIZE 一致
  const totalPages = Math.ceil(totalCount / pageSize)
  const hasNextPage = !!paginatedData?.next
  const hasPrevPage = !!paginatedData?.previous
  const hasSubscriptions = subscriptions.length > 0

  // 郵件通知狀態
  const {
    preferences,
    update: updatePreference,
    isUpdating,
    isLoading: isPreferencesLoading,
    isError: isPreferencesError,
  } = useUserPreferences()

  // 顯示狀態：
  // 1. 如果正在讀取，依賴 isLoading 顯示 spinner
  // 2. 如果讀取失敗 (isError) 或 data 為 undefined，則不應該預設為 true，這會誤導使用者
  // 這裡我們改為：如果有 data 就用 data.receive_email，否則暫時視為 false (避免發生錯誤時顯示為開啟)
  const emailEnabled = preferences?.receive_email ?? false

  // 切換全域郵件通知
  const toggleAllEmailNotifications = () => {
    if (isUpdating || isPreferencesLoading || isPreferencesError) return
    updatePreference({ receive_email: !emailEnabled })
  }

  // 生成頁碼按鈕列表
  const getPageNumbers = (): (number | 'ellipsis')[] => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }

    const pages: (number | 'ellipsis')[] = []
    if (currentPage <= 4) {
      // 靠近開頭：顯示 1 2 3 4 5 ... last
      for (let i = 1; i <= 5; i++) pages.push(i)
      pages.push('ellipsis', totalPages)
    } else if (currentPage >= totalPages - 3) {
      // 靠近結尾：顯示 1 ... last-4 last-3 last-2 last-1 last
      pages.push(1, 'ellipsis')
      for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i)
    } else {
      // 中間：顯示 1 ... current-1 current current+1 ... last
      pages.push(1, 'ellipsis')
      for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i)
      pages.push('ellipsis', totalPages)
    }
    return pages
  }

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
          <p className="text-white/90 text-lg">追蹤 {totalCount} 部漫畫</p>
        </div>
      </div>

      {/* Content */}
      <div className="container mx-auto px-4 py-8">
        {hasSubscriptions ? (
          <>
            <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <p className="text-gray-600">
                共 {totalCount} 部追蹤中的漫畫
                {paginatedData && ` · 第 ${currentPage} 頁`}
              </p>

              {/* 郵件通知設定 */}
              <div className="flex items-center gap-3 bg-white rounded-lg px-4 py-2 shadow-sm border border-gray-100">
                <div className="flex items-center gap-2">
                  <svg
                    className="w-5 h-5 text-gray-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                  <span className="text-sm text-gray-600">郵件通知</span>
                </div>
                {isPreferencesLoading ? (
                  <div className="w-11 h-6 flex items-center justify-center">
                    <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                ) : isPreferencesError ? (
                  <div
                    className="flex items-center text-red-500"
                    title="無法讀取設定"
                  >
                    <svg
                      className="w-6 h-6"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  </div>
                ) : (
                  <button
                    onClick={toggleAllEmailNotifications}
                    disabled={isUpdating || isPreferencesLoading}
                    aria-pressed={emailEnabled}
                    aria-label={
                      emailEnabled ? '關閉所有郵件通知' : '開啟所有郵件通知'
                    }
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                      emailEnabled ? 'bg-indigo-500' : 'bg-gray-300'
                    } ${isUpdating ? 'opacity-50 cursor-wait' : ''}`}
                    title={
                      emailEnabled ? '關閉所有郵件通知' : '開啟所有郵件通知'
                    }
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-md transition-transform ${
                        emailEnabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                )}
              </div>
            </div>

            {isLoadingSeries ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                <p className="ml-4 text-gray-600">載入漫畫資訊中...</p>
              </div>
            ) : (
              <>
                {/* 漫畫列表 - 使用 SeriesCard */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {seriesData.map(series => (
                    <SeriesCard key={series.id} series={series} />
                  ))}
                </div>

                {/* 分頁控制 */}
                {totalPages > 1 && (
                  <div className="mt-8 flex justify-center items-center gap-1">
                    {/* 首頁 */}
                    <button
                      onClick={() => setSearchParams({ page: '1' })}
                      disabled={currentPage === 1}
                      className="w-10 h-10 rounded-lg font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed text-gray-600 hover:bg-gray-100"
                      title="首頁"
                    >
                      «
                    </button>
                    {/* 上一頁 */}
                    <button
                      onClick={() =>
                        setSearchParams({ page: String(currentPage - 1) })
                      }
                      disabled={!hasPrevPage}
                      className="w-10 h-10 rounded-lg font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed text-gray-600 hover:bg-gray-100"
                      title="上一頁"
                    >
                      ‹
                    </button>

                    {/* 頁碼按鈕 */}
                    {getPageNumbers().map((page, index) =>
                      page === 'ellipsis' ? (
                        <span
                          key={`ellipsis-${index}`}
                          className="w-10 h-10 flex items-center justify-center text-gray-400"
                        >
                          …
                        </span>
                      ) : (
                        <button
                          key={page}
                          onClick={() =>
                            setSearchParams({ page: String(page) })
                          }
                          className={`w-10 h-10 rounded-full font-medium transition-all ${
                            page === currentPage
                              ? 'bg-gray-800 text-white shadow-md'
                              : 'text-gray-600 hover:bg-gray-100'
                          }`}
                        >
                          {page}
                        </button>
                      )
                    )}

                    {/* 下一頁 */}
                    <button
                      onClick={() =>
                        setSearchParams({ page: String(currentPage + 1) })
                      }
                      disabled={!hasNextPage}
                      className="w-10 h-10 rounded-lg font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed text-gray-600 hover:bg-gray-100"
                      title="下一頁"
                    >
                      ›
                    </button>
                    {/* 末頁 */}
                    <button
                      onClick={() =>
                        setSearchParams({ page: String(totalPages) })
                      }
                      disabled={currentPage === totalPages}
                      className="w-10 h-10 rounded-lg font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed text-gray-600 hover:bg-gray-100"
                      title="末頁"
                    >
                      »
                    </button>
                  </div>
                )}
              </>
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

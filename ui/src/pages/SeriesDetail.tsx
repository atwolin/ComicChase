import { useParams, useNavigate } from 'react-router-dom'
import { clsx } from 'clsx'
import { Loading } from '@/components/Loading'
import { ErrorDisplay } from '@/components/Error'
import { useSeriesDetail } from '@/hooks/useSeries'
import { useToggleSubscription } from '@/hooks/useSubscription'
import { useRequireAuth } from '@/hooks/useRequireAuth'
import type { Volume } from '@/api'

import {
  SERIES_STATUS_COLORS as statusColors,
  SERIES_STATUS_LABELS as statusLabels,
  REGION_LABELS as regionLabels,
} from '@/constants/series'
import { ROUTES } from '@/constants/routes'

// 漫畫詳情頁面
export const SeriesDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  const parsedId = id ? parseInt(id, 10) : NaN
  const seriesId = Number.isNaN(parsedId) ? undefined : parsedId

  // 資料取得
  const { data: series, isLoading, error, refetch } = useSeriesDetail(seriesId)

  // 認證狀態
  const { isAuthenticated, navigateToLogin } = useRequireAuth()

  // 追蹤功能（只在已登入且有有效 seriesId 時查詢）
  const {
    isSubscribed,
    toggle: toggleSubscription,
    isLoading: isTogglingSubscription,
  } = useToggleSubscription(seriesId, isAuthenticated)

  // 處理追蹤按鈕點擊
  const handleToggleSubscription = async () => {
    // 檢查是否已登入
    if (!isAuthenticated) {
      // 顯示通知詢問是否要登入
      const shouldLogin = window.confirm(
        '您需要登入才能追蹤此系列\n\n是否前往登入頁面？'
      )
      if (shouldLogin) {
        navigateToLogin()
      }
      return
    }

    // 已登入，執行追蹤/取消追蹤
    try {
      await toggleSubscription()
    } catch (error) {
      console.error('追蹤操作失敗:', error)
      alert('操作失敗，請稍後再試')
    }
  }

  // 處理返回按鈕
  const handleBack = () => {
    // 檢查是否有瀏覽器歷史
    if (window.history.length > 1) {
      navigate(-1) // 返回上一頁
    } else {
      navigate(ROUTES.SERIES_LIST) // 沒有歷史時返回列表頁
    }
  }

  // 載入中狀態
  if (isLoading || seriesId === undefined) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <Loading />
      </div>
    )
  }

  // 錯誤處理
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <ErrorDisplay
          message="無法載入漫畫詳情，請檢查網路連線"
          onRetry={refetch}
        />
      </div>
    )
  }

  // 找不到漫畫
  if (!series) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center">
            <p className="text-gray-500 text-lg mb-4">找不到此漫畫</p>
            <button
              onClick={handleBack}
              className="text-indigo-600 hover:text-indigo-700 underline"
            >
              返回
            </button>
          </div>
        </div>
      </div>
    )
  }

  // 根據地區分類單行本
  const volumesByRegion = {
    JP: series.volumes?.filter((v: Volume) => v.region === 'JP') || [],
    TW: series.volumes?.filter((v: Volume) => v.region === 'TW') || [],
  }

  const statusColorClass =
    statusColors[series.status_jp as keyof typeof statusColors] ||
    statusColors.default
  const statusText =
    statusLabels[series.status_jp as keyof typeof statusLabels] ||
    series.status_jp ||
    '狀態不明'

  // 封面圖片邏輯：優先使用台版最新單行本封面，沒有的話用日版
  const coverImageUrl =
    series.latest_volume_tw_image || series.latest_volume_jp_image

  // JSX 渲染
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Hero Section with Gradient Background */}
      <div className="relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative container mx-auto px-4 py-8">
          {/* Back Button */}
          <button
            onClick={handleBack}
            className="inline-flex items-center text-white/90 hover:text-white mb-6 transition-colors"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            返回列表
          </button>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Main Content Card */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-8 -mt-20 relative z-10">
          {' '}
          {/* 向上微移，創造覆蓋效果 */}
          {/* Header Section */}
          <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 p-8 border-b border-gray-200">
            <div className="flex flex-col md:flex-row gap-8">
              {/* Cover Image */}
              <div className="flex-shrink-0">
                {coverImageUrl ? (
                  <img
                    src={coverImageUrl}
                    alt={`${series.title_tw || series.title_jp} 封面`}
                    className="w-48 h-64 object-cover rounded-xl shadow-lg"
                  />
                ) : (
                  <div className="w-48 h-64 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-xl shadow-lg flex items-center justify-center">
                    <span className="text-white text-6xl">📚</span>
                  </div>
                )}
              </div>

              {/* Title and Info */}
              <div className="flex-1">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                      {series.title_tw || series.title_jp || '無標題'}
                    </h1>

                    {/* 狀態標籤和追蹤按鈕 */}
                    <div className="flex items-center gap-3 mb-4 flex-wrap">
                      {/* 狀態標籤 */}
                      <span
                        className={clsx(
                          'inline-flex items-center px-4 py-1.5 text-sm font-semibold rounded-full border',
                          statusColorClass
                        )}
                      >
                        {statusText}
                      </span>

                      {/* 追蹤按鈕 */}
                      <button
                        onClick={handleToggleSubscription}
                        disabled={isTogglingSubscription}
                        className={clsx(
                          'inline-flex items-center gap-2 px-4 py-1.5 text-sm font-semibold rounded-full border transition-all disabled:opacity-50 disabled:cursor-not-allowed',
                          isAuthenticated && isSubscribed
                            ? 'bg-gradient-to-r from-red-100 to-red-200 text-gray-800 hover:from-red-200 hover:to-red-300'
                            : 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700'
                        )}
                      >
                        {isTogglingSubscription ? (
                          <>
                            <svg
                              className="animate-spin h-4 w-4"
                              fill="none"
                              viewBox="0 0 24 24"
                            >
                              <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                strokeWidth="4"
                              ></circle>
                              <path
                                className="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                              ></path>
                            </svg>
                            處理中...
                          </>
                        ) : isAuthenticated && isSubscribed ? (
                          <>
                            <svg
                              className="w-5 h-5"
                              fill="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z"
                                fill="#ef4444"
                              />
                            </svg>
                            已追蹤
                          </>
                        ) : (
                          <>
                            <svg
                              className="w-5 h-5"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={1.5}
                                d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
                              />
                            </svg>
                            追蹤此系列
                          </>
                        )}
                      </button>
                    </div>

                    {series.title_tw && series.title_jp && (
                      <p className="text-xl text-gray-600 mb-4">
                        {series.title_jp}
                      </p>
                    )}
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 font-medium">作者：</span>
                    <span className="text-gray-900">
                      {series.author || '未知'}
                    </span>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-4 mt-6">
                    {series.latest_volume_jp_number && (
                      <div className="bg-white/60 backdrop-blur-sm p-4 rounded-xl border border-indigo-200">
                        <p className="text-sm text-gray-600 mb-1">
                          日版最新卷數
                        </p>
                        <p className="text-3xl font-bold text-indigo-600">
                          第 {series.latest_volume_jp_number} 卷
                        </p>
                      </div>
                    )}
                    {series.latest_volume_tw_number && (
                      <div className="bg-white/60 backdrop-blur-sm p-4 rounded-xl border border-purple-200">
                        <p className="text-sm text-gray-600 mb-1">
                          台版最新卷數
                        </p>
                        <p className="text-3xl font-bold text-purple-600">
                          第 {series.latest_volume_tw_number} 卷
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
          {/* Volumes Section */}
          {series.volumes && series.volumes.length > 0 && (
            <div className="p-8">
              <div className="space-y-8">
                {(['JP', 'TW'] as const).map(region => {
                  const volumes = volumesByRegion[region]
                  if (volumes.length === 0) return null

                  return (
                    <div key={region}>
                      <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                        <span
                          className={clsx(
                            'w-1 h-8 rounded-full',
                            region === 'JP'
                              ? 'bg-gradient-to-b from-indigo-500 to-purple-500'
                              : 'bg-gradient-to-b from-pink-500 to-rose-500'
                          )}
                        ></span>
                        {regionLabels[region]}版單行本
                        <span className="text-lg font-normal text-gray-500">
                          ({volumes.length} 卷)
                        </span>
                      </h2>
                      <div className="overflow-x-auto">
                        <div className="inline-block min-w-full align-middle">
                          <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 rounded-xl">
                            <table className="min-w-full divide-y divide-gray-300">
                              <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
                                <tr>
                                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700 uppercase tracking-wider w-1/12">
                                    卷數
                                  </th>
                                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700 uppercase tracking-wider w-2/12">
                                    版本
                                  </th>
                                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700 uppercase tracking-wider w-2/12">
                                    發售日期
                                  </th>
                                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700 uppercase tracking-wider w-3/12">
                                    出版社
                                  </th>
                                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700 uppercase tracking-wider w-4/12">
                                    ISBN
                                  </th>
                                </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                                {volumes.map((volume: Volume) => (
                                  <tr
                                    key={volume.id}
                                    className="hover:bg-gray-50 transition-colors"
                                  >
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                                      {volume.volume_number || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-base text-gray-700">
                                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-base font-medium bg-blue-100 text-blue-800">
                                        {volume.variant || '普通版'}
                                      </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-base text-gray-700">
                                      {volume.release_date
                                        ? new Date(
                                            volume.release_date
                                          ).toLocaleDateString('zh-TW', {
                                            year: 'numeric',
                                            month: '2-digit',
                                            day: '2-digit',
                                          })
                                        : '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                      {volume.publisher_name || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-mono">
                                      {volume.isbn || '-'}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
          {/* No Volumes Message */}
          {(!series.volumes || series.volumes.length === 0) && (
            <div className="p-8 text-center text-gray-500">
              <p>暫無單行本資料</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

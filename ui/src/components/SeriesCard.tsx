import { Link } from 'react-router-dom'
import type { SeriesList } from '@/api'
import { clsx } from 'clsx'
import { ROUTES } from '@/constants/routes'
import { useToggleSubscription } from '@/hooks/useSubscription'
import { useAuth } from '@/contexts/AuthContext'
import { useRequireAuth } from '@/hooks/useRequireAuth'

import {
  SERIES_STATUS_COLORS as statusColors,
  SERIES_STATUS_LABELS as statusLabels,
} from '@/constants/series'

interface SeriesCardProps {
  series: SeriesList
}

export const SeriesCard = ({ series }: SeriesCardProps) => {
  // 封面圖片邏輯：優先使用台版最新單行本封面，沒有的話用日版
  const imageUrl =
    series.latest_volume_tw_image || series.latest_volume_jp_image

  // 取得對應的狀態顏色和標籤
  const statusColor =
    statusColors[series.status_jp as keyof typeof statusColors] ||
    statusColors.default
  const statusLabel =
    statusLabels[series.status_jp as keyof typeof statusLabels] ||
    series.status_jp

  // 認證狀態
  const { isAuthenticated } = useAuth()
  const { navigateToLogin } = useRequireAuth()

  // 追蹤功能
  const {
    isSubscribed,
    toggle: toggleSubscription,
    isLoading: isTogglingSubscription,
  } = useToggleSubscription(series.id, isAuthenticated)

  // 處理愛心按鈕點擊
  const handleHeartClick = async (e: React.MouseEvent) => {
    e.preventDefault() // 阻止 Link 導航
    e.stopPropagation()

    if (!isAuthenticated) {
      const shouldLogin = window.confirm(
        '您需要登入才能追蹤此系列\n\n是否前往登入頁面？'
      )
      if (shouldLogin) {
        navigateToLogin()
      }
      return
    }

    try {
      await toggleSubscription()
    } catch (error) {
      console.error('追蹤操作失敗:', error)
    }
  }

  return (
    <Link
      to={ROUTES.SERIES_DETAIL(series.id)}
      className="block bg-white rounded-xl shadow-md hover:shadow-2xl transition-all duration-300 overflow-hidden group border border-gray-200 hover:border-indigo-300"
    >
      {/* Cover Image Logic */}
      <div className="w-full h-64 relative flex items-center justify-center overflow-hidden bg-gray-100">
        {imageUrl ? (
          // 如果有爬到圖片，顯示圖片
          <img
            src={imageUrl}
            alt={`${series.title_tw || series.title_jp} 封面`}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
          />
        ) : (
          // 沒有圖片，顯示層背景 + Emoji
          <div className="w-full h-full bg-gradient-to-br from-indigo-400 via-purple-500 to-pink-500 flex items-center justify-center">
            <span className="text-7xl group-hover:scale-110 transition-transform duration-300">
              📚
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-bold text-gray-900 line-clamp-2 flex-1 group-hover:text-indigo-600 transition-colors">
            {series.title_tw || series.title_jp}
          </h3>
          <div className="flex items-center gap-2 ml-2 flex-shrink-0">
            <span
              className={clsx(
                'px-2.5 py-1 text-xs font-semibold rounded-full border',
                statusColor
              )}
            >
              {statusLabel}
            </span>
            {/* 愛心追蹤按鈕 */}
            <button
              onClick={handleHeartClick}
              disabled={isTogglingSubscription}
              aria-label={
                isAuthenticated && isSubscribed ? '取消追蹤' : '追蹤此系列'
              }
              aria-pressed={isAuthenticated && isSubscribed}
              className={clsx(
                'p-1 rounded-full transition-all disabled:opacity-50',
                isAuthenticated && isSubscribed
                  ? 'hover:bg-red-50'
                  : 'hover:bg-gray-100'
              )}
              title={
                isAuthenticated && isSubscribed ? '取消追蹤' : '追蹤此系列'
              }
            >
              {isTogglingSubscription ? (
                <svg
                  className="animate-spin w-5 h-5 text-gray-400"
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
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : isAuthenticated && isSubscribed ? (
                // 紅色實心愛心 - 已追蹤
                <svg className="w-5 h-5" fill="#ef4444" viewBox="0 0 24 24">
                  <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
                </svg>
              ) : (
                // 空心愛心 - 未追蹤
                <svg
                  className="w-5 h-5 text-gray-400 hover:text-red-400 transition-colors"
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
              )}
            </button>
          </div>
        </div>

        {series.title_tw && series.title_jp && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-1">
            {series.title_jp}
          </p>
        )}

        <p className="text-sm text-gray-700 mb-4">作者：{series.author}</p>

        {/* 注意：SeriesList 類型沒有 latest_volume_jp_number 和 latest_volume_tw_number */}
        {/* 這些信息只在 SeriesDetail 頁面可用 */}
      </div>
    </Link>
  )
}

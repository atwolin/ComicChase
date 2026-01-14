import { Link } from 'react-router-dom'
import type { SeriesList } from '@/api'
import { clsx } from 'clsx'
import { ROUTES } from '@/constants/routes'

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
          <span
            className={clsx(
              'px-2.5 py-1 text-xs font-semibold rounded-full ml-2 flex-shrink-0 border',
              statusColor
            )}
          >
            {statusLabel}
          </span>
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

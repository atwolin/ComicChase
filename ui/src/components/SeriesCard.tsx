import { Link, useNavigate } from 'react-router-dom'
import type { Series } from '@/types'
import { clsx } from 'clsx'
import { useCollections, useAddCollection, useRemoveCollection } from '@/hooks/useCollections'
import { authApi } from '@/api/client'
import { useState } from 'react'

interface SeriesCardProps {
  series: Series
}

const statusLabels = {
  ongoing: '連載中',
  completed: '已完結',
  hiatus: '休刊中',
}

const statusColors = {
  ongoing: 'bg-green-500/20 text-green-700 border-green-500/30',
  completed: 'bg-gray-500/20 text-gray-700 border-gray-500/30',
  hiatus: 'bg-yellow-500/20 text-yellow-700 border-yellow-500/30',
  default: 'bg-gray-200 text-gray-600 border-gray-300', // 加入預設值以防 API 回傳未定義的狀態
}

export const SeriesCard = ({ series }: SeriesCardProps) => {
  const navigate = useNavigate()
  const [isAdding, setIsAdding] = useState(false)

  // 檢查是否已登入
  const isAuthenticated = authApi.isAuthenticated()

  // 只有登入後才獲取收藏列表
  const { data: collections } = useCollections({
    enabled: isAuthenticated,
  })
  const addCollection = useAddCollection()
  const removeCollection = useRemoveCollection()

  // 檢查該漫畫是否已在收藏中
  const isCollected = collections?.some(
    (collection) => collection.series.id === series.id
  ) || false
  const collectionId = collections?.find(
    (collection) => collection.series.id === series.id
  )?.id

  const handleToggleCollection = async (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    setIsAdding(true)
    try {
      if (isCollected && collectionId) {
        await removeCollection.mutateAsync(collectionId)
      } else {
        await addCollection.mutateAsync(series.id)
      }
    } catch (error) {
      console.error('收藏操作失敗:', error)
    } finally {
      setIsAdding(false)
    }
  }

  // 定義 imageUrl。
  // 後端還沒做圖片欄位叫做 'cover_image'，暫時設為 null
  const imageUrl = (series as any).cover_image || null;

  // 取得對應的狀態顏色，如果找不到則使用預設值
  const statusColor = statusColors[series.status_japan] || statusColors.default;
  const statusLabel = (statusLabels as any)[series.status_japan] || series.status_japan;

  return (
    <Link
      to={`/series/${series.id}`}
      className="group block bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-200 hover:border-indigo-300"
    >
      {/* Cover Image Logic */}
      <div className="w-full h-64 relative flex items-center justify-center overflow-hidden bg-gray-100">
        {imageUrl ? (
          // 如果有爬到圖片，顯示圖片
          <img
            src={imageUrl}
            alt="Comic Cover"
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
        {/* 收藏按鈕 - 懸浮在圖片右上角 */}
        <button
          onClick={handleToggleCollection}
          disabled={isAdding}
          className={clsx(
            'absolute top-2 right-2 p-2 rounded-full shadow-lg transition-all z-10',
            isAuthenticated && isCollected
              ? 'bg-white/90 hover:bg-white text-red-500'
              : 'bg-white/90 hover:bg-white text-gray-400 hover:text-red-500'
          )}
          title={
            !isAuthenticated
              ? '請先登入以加入收藏'
              : isCollected
              ? '移除收藏'
              : '加入收藏'
          }
        >
            {isAdding ? (
              <svg
                className="animate-spin h-5 w-5"
                xmlns="http://www.w3.org/2000/svg"
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
            ) : (
              <svg
                className="w-5 h-5"
                fill={isAuthenticated && isCollected ? 'currentColor' : 'none'}
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
            )}
          </button>
      </div>

      {/* Content */}
      <div className="p-5">
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-bold text-gray-900 line-clamp-2 flex-1 group-hover:text-indigo-600 transition-colors">
            {series.traditional_chinese_title || series.japanese_title}
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

        {series.traditional_chinese_title && series.japanese_title && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-1">
            {series.japanese_title}
          </p>
        )}

        <p className="text-sm text-gray-700 mb-4">作者：{series.author}</p>

        <div className="flex flex-col gap-2 text-xs">
          {series.latest_volume_jp_number && (
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
              <span className="text-gray-600">
                日版：第 <span className="font-semibold text-gray-900">{series.latest_volume_jp_number}</span> 卷
              </span>
            </div>
          )}
          {series.latest_volume_tw_number && (
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              <span className="text-gray-600">
                台版：第 <span className="font-semibold text-gray-900">{series.latest_volume_tw_number}</span> 卷
              </span>
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

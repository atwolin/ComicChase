import { useParams, Link, useNavigate } from 'react-router-dom'
import { useSeriesDetail } from '@/hooks/useSeries'
import { useCollections, useAddCollection, useRemoveCollection } from '@/hooks/useCollections'
import { Loading } from '@/components/Loading'
import { Error } from '@/components/Error'
import { clsx } from 'clsx'
import { authApi } from '@/api/client'
import { useState } from 'react'

// 狀態標籤對應
const statusLabels = {
  ongoing: '連載中',
  completed: '已完結',
  hiatus: '休刊中',
}

// 狀態顏色對應
const statusColors = {
  ongoing: 'bg-green-500/20 text-green-700 border-green-500/30',
  completed: 'bg-gray-500/20 text-gray-700 border-gray-500/30',
  hiatus: 'bg-yellow-500/20 text-yellow-700 border-yellow-500/30',
}

// 地區標籤對應
const regionLabels = {
  JP: '日本',
  TW: '台灣',
}

//  漫畫詳情頁面
export const SeriesDetail = () => {
  const { id } = useParams<{ id: string }>()
  const seriesId = id ? parseInt(id, 10) : 0
  const navigate = useNavigate()
  const [isAdding, setIsAdding] = useState(false)

  const { data: series, isLoading, error, refetch } = useSeriesDetail(seriesId)

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
    (collection) => collection.series.id === seriesId
  ) || false
  const collectionId = collections?.find(
    (collection) => collection.series.id === seriesId
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
        await addCollection.mutateAsync(seriesId)
      }
    } catch (error) {
      console.error('收藏操作失敗:', error)
    } finally {
      setIsAdding(false)
    }
  }

  // 載入中狀態
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <Loading />
      </div>
    )
  }

  // 錯誤狀態
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <Error message="無法載入漫畫詳情" onRetry={() => refetch()} />
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
            <Link
              to="/"
              className="text-indigo-600 hover:text-indigo-700 underline"
            >
              返回列表
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // 根據地區分類單行本
  const volumesByRegion = {
    JP: series.volumes?.filter((v) => v.region === 'JP') || [],
    TW: series.volumes?.filter((v) => v.region === 'TW') || [],
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Hero Section with Gradient Background */}
      <div className="relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative container mx-auto px-4 py-8">
          <Link
            to="/series"
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
          </Link>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Main Content Card */}
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-8">
          {/* Header Section */}
          <div className="bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 p-8 border-b border-gray-200">
            <div className="flex flex-col md:flex-row gap-8">
              {/* Cover Image Placeholder */}
              <div className="flex-shrink-0">
                <div className="w-48 h-64 bg-gradient-to-br from-indigo-400 to-purple-500 rounded-xl shadow-lg flex items-center justify-center">
                  <span className="text-white text-6xl">📚</span>
                </div>
              </div>

              {/* Title and Info */}
              <div className="flex-1">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                      {series.traditional_chinese_title || series.japanese_title}
                    </h1>
                    {series.traditional_chinese_title && series.japanese_title && (
                      <p className="text-xl text-gray-600 mb-4">
                        {series.japanese_title}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {isAuthenticated && (
                      <button
                        onClick={handleToggleCollection}
                        disabled={isAdding}
                        className={clsx(
                          'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all shadow-md',
                          isCollected
                            ? 'bg-red-500 hover:bg-red-600 text-white'
                            : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                        )}
                        title={isCollected ? '移除收藏' : '加入收藏'}
                      >
                        {isAdding ? (
                          <>
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
                            <span>處理中...</span>
                          </>
                        ) : (
                          <>
                            <svg
                              className="w-5 h-5"
                              fill={isCollected ? 'currentColor' : 'none'}
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                              />
                            </svg>
                            <span>{isCollected ? '已收藏' : '加入收藏'}</span>
                          </>
                        )}
                      </button>
                    )}
                    <span
                      className={clsx(
                        'px-4 py-2 text-sm font-semibold rounded-full border',
                        statusColors[series.status_japan]
                      )}
                    >
                      {statusLabels[series.status_japan]}
                    </span>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 font-medium">作者：</span>
                    <span className="text-gray-900">{series.author}</span>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-4 mt-6">
                    {series.latest_volume_jp_number && (
                      <div className="bg-white/60 backdrop-blur-sm p-4 rounded-xl border border-indigo-200">
                        <p className="text-sm text-gray-600 mb-1">日版最新卷數</p>
                        <p className="text-3xl font-bold text-indigo-600">
                          第 {series.latest_volume_jp_number} 卷
                        </p>
                      </div>
                    )}
                    {series.latest_volume_tw_number && (
                      <div className="bg-white/60 backdrop-blur-sm p-4 rounded-xl border border-purple-200">
                        <p className="text-sm text-gray-600 mb-1">台版最新卷數</p>
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
                {(['JP', 'TW'] as const).map((region) => {
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
                                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                    卷數
                                  </th>
                                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                    版本
                                  </th>
                                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                    發售日期
                                  </th>
                                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                    出版社
                                  </th>
                                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                                    ISBN
                                  </th>
                                </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                                {volumes.map((volume) => (
                                  <tr
                                    key={volume.id}
                                    className="hover:bg-gray-50 transition-colors"
                                  >
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">
                                      {volume.volume_number || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                        {volume.variant || '普通版'}
                                      </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                      {volume.release_date
                                        ? new Date(volume.release_date).toLocaleDateString(
                                            'zh-TW'
                                          )
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

          {(!series.volumes || series.volumes.length === 0) && (
            <div className="p-8 text-center text-gray-500">
              <p>暫無單行本</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

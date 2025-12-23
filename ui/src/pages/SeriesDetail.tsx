import { useParams, Link } from 'react-router-dom'
import { clsx } from 'clsx'
import { Loading } from '@/components/Loading'
import { ErrorDisplay } from '@/components/Error'
import { useSeriesDetail } from '@/hooks/useSeries'

import {
  SERIES_STATUS_COLORS as statusColors,
  SERIES_STATUS_LABELS as statusLabels,
  REGION_LABELS as regionLabels,
} from '@/constants/series'
import type { Volume } from '@/types'
import { ROUTES } from '@/constants/routes'

// 漫畫詳情頁面
export const SeriesDetail = () => {
  const { id } = useParams()
  const parsedId = id ? parseInt(id, 10) : NaN
  const seriesId = Number.isNaN(parsedId) ? undefined : parsedId

  // 資料取得
  const { data: series, isLoading, error, refetch } = useSeriesDetail(seriesId)

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
        <ErrorDisplay message="無法載入漫畫詳情" onRetry={() => refetch()} />
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
              to={ROUTES.SERIES_LIST}
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
    JP: series.volumes?.filter((v: Volume) => v.region === 'JP') || [],
    TW: series.volumes?.filter((v: Volume) => v.region === 'TW') || [],
  }

  const statusColorClass =
    statusColors[series.status_japan] || statusColors.default
  const statusText =
    statusLabels[series.status_japan] || series.status_japan || '狀態不明'

  // JSX 渲染
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Hero Section with Gradient Background */}
      <div className="relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative container mx-auto px-4 py-8">
          {/* Back Button */}
          <Link
            to={ROUTES.SERIES_LIST}
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
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-8 -mt-20 relative z-10">
          {' '}
          {/* 向上微移，創造覆蓋效果 */}
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
                      {series.traditional_chinese_title ||
                        series.japanese_title ||
                        '無標題'}
                    </h1>
                    {/* 狀態標籤位置 */}
                    <span
                      className={clsx(
                        'inline-flex items-center px-4 py-1.5 text-sm font-semibold rounded-full border mb-4',
                        statusColorClass
                      )}
                    >
                      {statusText}
                    </span>
                    {/* ------------------ */}
                    {series.traditional_chinese_title &&
                      series.japanese_title && (
                        <p className="text-xl text-gray-600 mb-4">
                          {series.japanese_title}
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

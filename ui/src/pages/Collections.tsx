import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { SeriesCard } from '@/components/SeriesCard'
import { Loading } from '@/components/Loading'
import { Error } from '@/components/Error'
import { useCollections } from '@/hooks/useCollections'
import { authApi } from '@/api/client'

export const Collections = () => {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('all')

  // 檢查是否已登入
  if (!authApi.isAuthenticated()) {
    navigate('/login')
    return null
  }

  const { data: collections, isLoading, error } = useCollections()

  const filteredCollections = useMemo(() => {
    if (!collections) return []

    // 按照加入收藏的時間排序，最新的在前
    const sortedCollections = [...collections].sort((a, b) => {
      const dateA = new Date(a.created_at).getTime()
      const dateB = new Date(b.created_at).getTime()
      return dateB - dateA // 降序：最新的在前
    })

    // 篩選收藏
    return sortedCollections
      .map((collection) => collection.series)
      .filter((series) => {
        const matchesSearch =
          !searchQuery ||
          series.traditional_chinese_title
            ?.toLowerCase()
            .includes(searchQuery.toLowerCase()) ||
          series.japanese_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          series.author.toLowerCase().includes(searchQuery.toLowerCase())

        const matchesStatus =
          filterStatus === 'all' ||
          (filterStatus === 'ongoing' && series.status_japan === 'ongoing') ||
          (filterStatus === 'completed' && series.status_japan === 'completed') ||
          (filterStatus === 'hiatus' && series.status_japan === 'hiatus')

        return matchesSearch && matchesStatus
      })
  }, [collections, searchQuery, filterStatus])

  if (isLoading) {
    return <Loading />
  }

  if (error) {
    return <Error message="無法載入收藏列表" onRetry={() => {}} />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <span className="text-5xl">⭐</span>
            我的收藏
          </h1>
          <p className="text-gray-600">管理您收藏的漫畫，追蹤進度</p>
        </div>

        {/* Search Bar - 小尺寸 */}
        <div className="mb-6">
          <div className="max-w-md">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="搜尋收藏的漫畫..."
                className="w-full px-4 py-2 pl-10 pr-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
              />
              <div className="absolute inset-y-0 left-0 flex items-center pl-3">
                <svg
                  className="w-5 h-5 text-gray-400"
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
              </div>
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                filterStatus === 'all'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              全部
            </button>
            <button
              onClick={() => setFilterStatus('ongoing')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                filterStatus === 'ongoing'
                  ? 'bg-green-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              連載中
            </button>
            <button
              onClick={() => setFilterStatus('completed')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                filterStatus === 'completed'
                  ? 'bg-gray-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              已完結
            </button>
            <button
              onClick={() => setFilterStatus('hiatus')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                filterStatus === 'hiatus'
                  ? 'bg-yellow-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              休刊中
            </button>
          </div>
        </div>

        {/* Collections List */}
        {!collections || collections.length === 0 ? (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <div className="text-6xl mb-4">📚</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              還沒有收藏任何漫畫
            </h2>
            <p className="text-gray-600 mb-6">
              開始探索並收藏您喜愛的漫畫吧！
            </p>
            <Link
              to="/series"
              className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors shadow-md"
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
        ) : filteredCollections.length === 0 ? (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <div className="text-4xl mb-4">🔍</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              沒有找到匹配的收藏
            </h2>
            <p className="text-gray-600">嘗試調整搜索條件或篩選器</p>
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-600">
              共找到 {filteredCollections.length} 部漫畫
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredCollections.map((series) => (
                <SeriesCard key={series.id} series={series} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

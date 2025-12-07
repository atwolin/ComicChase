import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useSeriesList } from '@/hooks/useSeries'
import { SeriesCard } from '@/components/SeriesCard'
import { SearchBar } from '@/components/SearchBar'
import { FilterPanel, type FilterOptions } from '@/components/FilterPanel'
import { Loading } from '@/components/Loading'
import { Error } from '@/components/Error'

export const SeriesList = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '')
  const [ordering, setOrdering] = useState<string>('-id') // 默认按最新更新排序
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<FilterOptions>({
    status_jp: searchParams.get('status_jp') as any || '',
    category: searchParams.get('category') as any || '',
    genre: searchParams.get('genre') || '',
    year: searchParams.get('year') || '',
  })

  useEffect(() => {
    const searchParam = searchParams.get('search')
    if (searchParam !== null) {
      setSearchQuery(searchParam)
    }
  }, [searchParams])

  const params = useMemo(
    () => ({
      search: searchQuery || undefined,
      ordering,
      page,
      page_size: 20,
      ...(filters.status_jp && { status_jp: filters.status_jp }),
      ...(filters.category && { category: filters.category }),
      ...(filters.genre && { genre: filters.genre }),
      ...(filters.year && { year: filters.year }),
    }),
    [searchQuery, ordering, page, filters]
  )

  const { data, isLoading, error, refetch } = useSeriesList(params)

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setPage(1)
    if (query) {
      setSearchParams({ search: query })
    } else {
      setSearchParams({})
    }
  }

  const handleOrderingChange = (newOrdering: string) => {
    setOrdering(newOrdering)
    setPage(1)
  }

  const handleFilterChange = (newFilters: FilterOptions) => {
    setFilters(newFilters)
    setPage(1)
    // 更新 URL 搜尋參數
    const newParams = new URLSearchParams()
    if (searchQuery) newParams.set('search', searchQuery)
    Object.entries(newFilters).forEach(([key, value]) => {
      if (value && value !== '') {
        newParams.set(key, value.toString())
      }
    })
    setSearchParams(newParams)
  }

  const handleResetFilters = () => {
    setFilters({})
    setPage(1)
    const newParams = new URLSearchParams()
    if (searchQuery) newParams.set('search', searchQuery)
    setSearchParams(newParams)
  }

  if (isLoading) {
    return <Loading />
  }

  if (error) {
    return <Error message="無法載入漫畫列表" onRetry={() => refetch()} />
  }

  if (!data) {
    return null
  }

  const totalPages = Math.ceil(data.count / 20)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        {/* 搜索栏 - 最上面 */}
        <div className="mb-6">
          <SearchBar onSearch={handleSearch} initialValue={searchQuery} />
        </div>

        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <span className="w-1 h-10 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></span>
            漫畫列表
          </h1>

          <FilterPanel
            filters={filters}
            onFilterChange={handleFilterChange}
            onReset={handleResetFilters}
          />

          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="flex items-center gap-2">
              <label htmlFor="ordering" className="text-sm font-medium text-gray-700">
                排序方式：
              </label>
              <select
                id="ordering"
                value={ordering}
                onChange={(e) => handleOrderingChange(e.target.value)}
                className="px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
              >
                <option value="-id">最新更新</option>
                <option value="id">最舊更新</option>
                <option value="title_tw">中文標題</option>
                <option value="-title_tw">中文標題（降序）</option>
                <option value="title_jp">日文標題</option>
                <option value="-title_jp">日文標題（降序）</option>
                <option value="first_published_year">出版年份</option>
                <option value="-first_published_year">出版年份（降序）</option>
              </select>
            </div>

            <div className="text-sm text-gray-600">
              共 {data.count} 部漫畫
            </div>
          </div>
        </div>

        {data.results.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">找不到符合條件的漫畫</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
              {data.results.map((series) => (
                <SeriesCard key={series.id} series={series} />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="flex justify-center items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors shadow-sm"
                >
                  上一頁
                </button>
                <span className="px-4 py-2 text-gray-700">
                  第 {page} 頁 / 共 {totalPages} 頁
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-white border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors shadow-sm"
                >
                  下一頁
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { SeriesCard } from '@/components/SeriesCard'
import { Loading } from '@/components/Loading'
import { ErrorDisplay } from '@/components/Error'
import { useSeriesList } from '@/hooks/useSeries'

export const SeriesList = () => {
  const [searchParams] = useSearchParams()
  const [searchQuery, setSearchQuery] = useState(
    searchParams.get('search') || ''
  )
  const [page, setPage] = useState(1)
  const pageSize = 12 // 後端默認 page_size

  useEffect(() => {
    const searchParam = searchParams.get('search')
    setSearchQuery(searchParam ?? '')
    setPage(1)
  }, [searchParams])

  const params = useMemo(
    () => ({
      search: searchQuery || undefined,
      ordering: '-id', // 固定為預設排序：最新更新
      page,
      // 注意：後端 API 目前不支持 page_size 參數，使用默認值 12
    }),
    [searchQuery, page]
  )

  const { data, isLoading, error, refetch } = useSeriesList(params)

  // 生成頁碼按鈕列表
  const getPageNumbers = (
    currentPage: number,
    totalPages: number
  ): (number | 'ellipsis')[] => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }

    const pages: (number | 'ellipsis')[] = []
    if (currentPage <= 4) {
      for (let i = 1; i <= 5; i++) pages.push(i)
      pages.push('ellipsis', totalPages)
    } else if (currentPage >= totalPages - 3) {
      pages.push(1, 'ellipsis')
      for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i)
    } else {
      pages.push(1, 'ellipsis')
      for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i)
      pages.push('ellipsis', totalPages)
    }
    return pages
  }

  if (isLoading) {
    return <Loading />
  }

  if (error) {
    return <ErrorDisplay message="無法載入漫畫列表" onRetry={() => refetch()} />
  }

  if (!data) {
    return null
  }

  const totalPages = Math.ceil(data.count / pageSize) // 後端默認 page_size 是 12

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <span className="w-1 h-10 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></span>
            漫畫列表
          </h1>

          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="text-sm text-gray-600">共 {data.count} 部漫畫</div>
          </div>
        </div>

        {data.results.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">找不到符合條件的漫畫</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
              {data.results.map(series => (
                <SeriesCard key={series.id} series={series} />
              ))}
            </div>

            {/* 分頁控制 */}
            {totalPages > 1 && (
              <div className="flex justify-center items-center gap-1">
                {/* 首頁 */}
                <button
                  onClick={() => setPage(1)}
                  disabled={page === 1}
                  className="w-10 h-10 rounded-lg font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed text-gray-600 hover:bg-gray-100"
                  title="首頁"
                >
                  «
                </button>
                {/* 上一頁 */}
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="w-10 h-10 rounded-lg font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed text-gray-600 hover:bg-gray-100"
                  title="上一頁"
                >
                  ‹
                </button>

                {/* 頁碼按鈕 */}
                {getPageNumbers(page, totalPages).map((pageNum, index) =>
                  pageNum === 'ellipsis' ? (
                    <span
                      key={`ellipsis-${index}`}
                      className="w-10 h-10 flex items-center justify-center text-gray-400"
                    >
                      …
                    </span>
                  ) : (
                    <button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      className={`w-10 h-10 rounded-full font-medium transition-all ${
                        pageNum === page
                          ? 'bg-gray-800 text-white shadow-md'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      {pageNum}
                    </button>
                  )
                )}

                {/* 下一頁 */}
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="w-10 h-10 rounded-lg font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed text-gray-600 hover:bg-gray-100"
                  title="下一頁"
                >
                  ›
                </button>
                {/* 末頁 */}
                <button
                  onClick={() => setPage(totalPages)}
                  disabled={page === totalPages}
                  className="w-10 h-10 rounded-lg font-medium transition-all disabled:opacity-30 disabled:cursor-not-allowed text-gray-600 hover:bg-gray-100"
                  title="末頁"
                >
                  »
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

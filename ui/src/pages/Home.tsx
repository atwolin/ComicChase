import { Link } from 'react-router-dom'
import { useSeriesList } from '@/hooks/useSeries'
import { SeriesCard } from '@/components/SeriesCard'
import { SearchBar } from '@/components/SearchBar'
import { Loading } from '@/components/Loading'
import { Error } from '@/components/Error'

export const Home = () => {
  const {
    data: latestData,
    isLoading: latestLoading,
    isError: latestError,
    refetch: retryLatest
  } = useSeriesList({
    ordering: '-id',
    page: 1,
    page_size: 12,
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative container mx-auto px-4 py-20 md:py-32">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 drop-shadow-lg">
              ComicChase
            </h1>
            <p className="text-xl md:text-2xl text-white/90 mb-8 drop-shadow-md">
              追蹤您喜愛的台日漫畫最新進度
            </p>
            <div className="max-w-2xl mx-auto">
              <SearchBar navigateOnSearch={true} initialValue="" />
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-12">
        {/* 最新更新 */}
        <section className="mb-16">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <span className="w-1 h-8 bg-gradient-to-b from-pink-500 to-rose-500 rounded-full"></span>
              最新更新
            </h2>
            <Link
              to="/series"
              className="text-indigo-600 hover:text-indigo-700 font-medium flex items-center gap-1 transition-colors"
            >
              查看全部
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
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Link>
          </div>

          {latestLoading ? (
            <Loading />
          ) : latestError ? (
            // 如果發生錯誤，顯示 Error 並傳入重試函式
            <Error message="無法載入最新漫畫，請檢查網路連線" onRetry={retryLatest} />
          ) : latestData?.results && latestData.results.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {latestData.results.slice(0, 8).map((series) => (
                <SeriesCard key={series.id} series={series} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              暫無最新更新
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

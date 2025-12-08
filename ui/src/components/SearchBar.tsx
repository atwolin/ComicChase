import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

interface SearchBarProps {
  onSearch?: (query: string) => void
  initialValue?: string
  navigateOnSearch?: boolean
  onFilterClick?: () => void // 點擊篩選按鈕的回呼函式
  hasActiveFilters?: boolean
}
// 搜尋列元件
export const SearchBar = ({
  onSearch,
  initialValue = '',
  navigateOnSearch = false,
  onFilterClick,
  hasActiveFilters = false
}: SearchBarProps) => {
  const [query, setQuery] = useState(initialValue)
  const navigate = useNavigate()

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (navigateOnSearch && query.trim()) {
      navigate(`/series?search=${encodeURIComponent(query.trim())}`)
    } else if (onSearch) {
      onSearch(query)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜尋漫畫標題或作者..."
          className="w-full px-4 py-3 pl-12 pr-20 bg-white/95 backdrop-blur-sm border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent shadow-lg text-gray-900 placeholder-gray-500"
        />
        <div className="absolute inset-y-0 left-0 flex items-center pl-4">
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
        <div className="absolute inset-y-0 right-0 flex items-center gap-2 pr-2">
          {onFilterClick && (
            <button
              type="button"
              onClick={onFilterClick}
              className="relative p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
              title="篩選條件"
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
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                />
              </svg>
              {hasActiveFilters && (
                <span className="absolute top-1 right-1 w-2 h-2 bg-indigo-600 rounded-full"></span>
              )}
            </button>
          )}
          {query && (
            <button
              type="button"
              onClick={() => {
                setQuery('')
                if (onSearch) onSearch('')
              }}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors"
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
    </form>
  )
}




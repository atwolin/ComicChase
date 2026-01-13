import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { buildSeriesSearchUrl } from '@/constants/routes'

interface SearchBarProps {
  onSearch?: (query: string) => void
  initialValue?: string
  navigateOnSearch?: boolean
  compact?: boolean // 緊湊模式，用於 Navbar
}

// 搜尋列元件
export const SearchBar = ({
  onSearch,
  initialValue = '',
  navigateOnSearch = false,
  compact = false,
}: SearchBarProps) => {
  const [query, setQuery] = useState(initialValue)
  const navigate = useNavigate()

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (navigateOnSearch && query.trim()) {
      navigate(buildSeriesSearchUrl(query))
    } else if (onSearch) {
      onSearch(query)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={compact ? 'w-full' : 'w-full max-w-2xl mx-auto'}
    >
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder={compact ? '搜尋漫畫...' : '搜尋漫畫標題或作者...'}
          className={
            compact
              ? 'w-full px-3 py-2 pl-10 pr-10 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm text-gray-900 placeholder-gray-400'
              : 'w-full px-4 py-3 pl-12 pr-20 bg-white/95 backdrop-blur-sm border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent shadow-lg text-gray-900 placeholder-gray-500'
          }
        />
        <div
          className={
            compact
              ? 'absolute inset-y-0 left-0 flex items-center pl-3'
              : 'absolute inset-y-0 left-0 flex items-center pl-4'
          }
        >
          <svg
            className={
              compact ? 'w-4 h-4 text-gray-400' : 'w-5 h-5 text-gray-400'
            }
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
        {query && (
          <div
            className={
              compact
                ? 'absolute inset-y-0 right-0 flex items-center pr-2'
                : 'absolute inset-y-0 right-0 flex items-center gap-2 pr-2'
            }
          >
            <button
              type="button"
              onClick={() => {
                setQuery('')
                if (onSearch) onSearch('')
              }}
              className={
                compact
                  ? 'p-1 text-gray-400 hover:text-gray-600 rounded transition-colors'
                  : 'p-2 text-gray-400 hover:text-gray-600 rounded-lg transition-colors'
              }
            >
              <svg
                className={compact ? 'w-4 h-4' : 'w-5 h-5'}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        )}
      </div>
    </form>
  )
}

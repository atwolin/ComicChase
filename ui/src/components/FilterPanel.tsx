import { useState } from 'react'
import { clsx } from 'clsx'

export interface FilterOptions {
  status_jp?: 'ongoing' | 'completed' | 'hiatus' | ''
  genre?: string
  year?: string
}

interface FilterPanelProps {
  filters: FilterOptions
  onFilterChange: (filters: FilterOptions) => void
  onReset: () => void
}

const genres = [
  { value: 'action', label: '動作' },
  { value: 'adventure', label: '冒險' },
  { value: 'comedy', label: '喜劇' },
  { value: 'drama', label: '劇情' },
  { value: 'fantasy', label: '奇幻' },
  { value: 'horror', label: '恐怖' },
  { value: 'mystery', label: '懸疑' },
  { value: 'romance', label: '戀愛' },
  { value: 'sci_fi', label: '科幻' },
  { value: 'slice_of_life', label: '日常' },
  { value: 'sports', label: '運動' },
  { value: 'supernatural', label: '超自然' },
]

const statuses = [
  { value: 'ongoing', label: '連載中' },
  { value: 'completed', label: '已完結' },
  { value: 'hiatus', label: '休刊中' },
]

// 根據年份（30年）
const currentYear = new Date().getFullYear()
const years = Array.from({ length: 30 }, (_, i) => currentYear - i)

export const FilterPanel = ({ filters, onFilterChange, onReset }: FilterPanelProps) => {
  const [isOpen, setIsOpen] = useState(false)

  const handleChange = (key: keyof FilterOptions, value: string) => {
    onFilterChange({
      ...filters,
      [key]: value || undefined,
    })
  }

  const hasActiveFilters = Object.values(filters).some((v) => v && v !== '')

  return (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors shadow-sm"
        >
          <svg
            className={clsx('w-5 h-5 transition-transform', isOpen && 'rotate-180')}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
          <span className="font-medium">篩選條件</span>
          {hasActiveFilters && (
            <span className="px-2 py-0.5 bg-indigo-600 text-white text-xs rounded-full">
              {Object.values(filters).filter((v) => v && v !== '').length}
            </span>
          )}
        </button>
        {hasActiveFilters && (
          <button
            onClick={onReset}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            清除所有
          </button>
        )}
      </div>

      {isOpen && (
        <div className="bg-white rounded-xl shadow-md p-6 border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* 連載狀態 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                連載狀態
              </label>
              <select
                value={filters.status_jp || ''}
                onChange={(e) => handleChange('status_jp', e.target.value)}
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
              >
                <option value="">全部</option>
                {statuses.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 類型 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                類型
              </label>
              <select
                value={filters.genre || ''}
                onChange={(e) => handleChange('genre', e.target.value)}
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
              >
                <option value="">全部</option>
                {genres.map((genre) => (
                  <option key={genre.value} value={genre.value}>
                    {genre.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 年份 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                出版年份
              </label>
              <select
                value={filters.year || ''}
                onChange={(e) => handleChange('year', e.target.value)}
                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm"
              >
                <option value="">全部</option>
                {years.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


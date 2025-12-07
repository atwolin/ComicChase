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

// 篩選面板元件
interface FilterPanelProps {
  filters: FilterOptions
  onFilterChange: (filters: FilterOptions) => void
  onReset: () => void
  isOpen?: boolean
  onToggle?: () => void
  position?: 'relative' | 'absolute'
}

export const FilterPanel = ({
  filters,
  onFilterChange,
  onReset,
  isOpen: controlledIsOpen,
  onToggle,
  position = 'relative'
}: FilterPanelProps) => {
  const [internalIsOpen, setInternalIsOpen] = useState(false)
  const isOpen = controlledIsOpen !== undefined ? controlledIsOpen : internalIsOpen
  const setIsOpen = onToggle || setInternalIsOpen

  const handleChange = (key: keyof FilterOptions, value: string) => {
    onFilterChange({
      ...filters,
      [key]: value || undefined,
    })
  }

  const hasActiveFilters = Object.values(filters).some((v) => v && v !== '')

  const panelContent = (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 z-50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">篩選條件</h3>
        {hasActiveFilters && (
          <button
            onClick={onReset}
            className="px-3 py-1 text-sm text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 rounded-lg transition-colors"
          >
            清除所有
          </button>
        )}
      </div>
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
  )

  if (position === 'absolute') {
    return (
      <>
        {isOpen && (
          <div className="absolute top-full left-0 right-0 mt-2">
            {panelContent}
          </div>
        )}
      </>
    )
  }

  return (
    <div className="mb-6">
      {isOpen && panelContent}
    </div>
  )
}


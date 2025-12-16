export const SERIES_STATUS = {
  ONGOING: 'ongoing',
  COMPLETED: 'completed',
  HIATUS: 'hiatus',
} as const

export type SeriesStatus = (typeof SERIES_STATUS)[keyof typeof SERIES_STATUS]

export const SERIES_STATUS_LABELS: Record<SeriesStatus, string> = {
  [SERIES_STATUS.ONGOING]: '連載中',
  [SERIES_STATUS.COMPLETED]: '已完結',
  [SERIES_STATUS.HIATUS]: '休刊中',
}

export const SERIES_STATUS_COLORS: Record<SeriesStatus, string> & {
  default: string
} = {
  [SERIES_STATUS.ONGOING]: 'bg-green-500/20 text-green-700 border-green-500/30',
  [SERIES_STATUS.COMPLETED]: 'bg-gray-500/20 text-gray-700 border-gray-500/30',
  [SERIES_STATUS.HIATUS]:
    'bg-yellow-500/20 text-yellow-700 border-yellow-500/30',
  default: 'bg-gray-200 text-gray-600 border-gray-300',
}

export const REGION_LABELS = {
  JP: '日本',
  TW: '台灣',
} as const

import { useSearchParams, Link } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { accountsUnsubscribeRetrieve, accountsUnsubscribeCreate } from '@/api'
import { ROUTES } from '@/constants/routes'

export const Unsubscribe = () => {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  // 1. Validate Token on mount
  const {
    data: validationData,
    isLoading: isValidating,
    isError: isValidationError,
  } = useQuery({
    queryKey: ['unsubscribe', token],
    queryFn: async () => {
      const { data } = await accountsUnsubscribeRetrieve({
        query: { token: token! },
      })
      return data
    },
    enabled: !!token,
    retry: false,
  })

  // 2. Unsubscribe Mutation
  const {
    mutate: doUnsubscribe,
    isPending: isSubmitting,
    isSuccess: isSuccess,
    isError: isSubmitError,
  } = useMutation({
    mutationFn: async () => {
      const { data } = await accountsUnsubscribeCreate({
        body: { token: token! },
      })
      return data
    },
  })

  // --- Render Helpers ---

  if (!token) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center p-4">
        <h1 className="text-2xl font-bold text-gray-800">無效的連結</h1>
        <p className="mt-2 text-gray-600">連結中缺少必要的驗證代碼。</p>
        <Link to={ROUTES.HOME} className="mt-4 text-blue-600 hover:underline">
          回首頁
        </Link>
      </div>
    )
  }

  if (isValidating) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center p-4">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
        <p className="mt-4 text-gray-600">驗證連結中...</p>
      </div>
    )
  }

  if (isValidationError || (validationData && !validationData.email)) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center p-4">
        <h1 className="text-2xl font-bold text-red-600">連結已失效或錯誤</h1>
        <p className="mt-2 text-gray-600">
          此取消訂閱連結可能已經過期或不正確。
        </p>
        <Link to={ROUTES.HOME} className="mt-4 text-blue-600 hover:underline">
          回首頁
        </Link>
      </div>
    )
  }

  if (isSuccess) {
    return (
      <div className="flex min-h-[50vh] flex-col items-center justify-center p-4">
        <div className="mb-4 rounded-full bg-green-100 p-4">
          <svg
            className="h-10 w-10 text-green-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-800">取消訂閱成功</h1>
        <p className="mt-2 text-center text-gray-600">
          <span className="font-semibold">{validationData?.email}</span>{' '}
          將不再收到每週新書通知。
        </p>
        <Link
          to={ROUTES.HOME}
          className="mt-6 rounded bg-blue-600 px-6 py-2 text-white hover:bg-blue-700"
        >
          回首頁
        </Link>
      </div>
    )
  }

  return (
    <div className="mx-auto mt-10 max-w-md rounded-lg bg-white p-8 shadow-md">
      <h1 className="mb-4 text-2xl font-bold text-gray-800">確認取消訂閱？</h1>
      <p className="mb-6 text-gray-600">
        您即將取消{' '}
        <span className="font-semibold text-gray-900">
          {validationData?.email}
        </span>{' '}
        的每週新書通知電子郵件。
        <br />
        <span className="mt-2 block text-sm text-gray-500">
          (您之後仍可隨時在設定頁面重新開啟)
        </span>
      </p>

      {isSubmitError && (
        <div className="mb-4 rounded bg-red-50 p-3 text-sm text-red-600">
          取消訂閱失敗，請稍後再試。
        </div>
      )}

      <div className="flex flex-col gap-3">
        <button
          onClick={() => doUnsubscribe()}
          disabled={isSubmitting}
          className="rounded bg-red-600 px-4 py-2 font-bold text-white transition hover:bg-red-700 disabled:opacity-50"
        >
          {isSubmitting ? '處理中...' : '確認取消訂閱'}
        </button>
        <Link
          to={ROUTES.HOME}
          className="rounded border border-gray-300 px-4 py-2 text-center text-gray-700 hover:bg-gray-50"
        >
          保留訂閱
        </Link>
      </div>
    </div>
  )
}

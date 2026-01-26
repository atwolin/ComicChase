import { useState, FormEvent, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { login } from '@/lib/allauth'
import { useAuth } from '@/contexts/AuthContext'
import { ROUTES } from '@/constants/routes'

export const Login = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { isAuthenticated } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // 如果已登入，重定向到首頁（使用 useEffect 避免渲染期間的副作用）
  useEffect(() => {
    if (isAuthenticated) {
      const redirectTo = searchParams.get('redirect') || ROUTES.HOME
      navigate(redirectTo, { replace: true })
    }
  }, [isAuthenticated, navigate, searchParams])

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const result = await login(email, password)

      if (result.status === 200) {
        // 登入成功，Custom Event 會自動更新 AuthContext
        // 導向 redirect 參數指定的頁面，或首頁
        const redirectTo = searchParams.get('redirect') || ROUTES.HOME
        navigate(redirectTo)
      } else {
        // 顯示錯誤訊息
        const errorMessage =
          result.errors?.[0]?.message || '登入失敗，請檢查帳號密碼'
        setError(errorMessage)
      }
    } catch (err: unknown) {
      console.error('Login error:', err)
      setError('登入失敗，請稍後再試')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* 卡片容器 */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* 標題 */}
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              登入 ComicChase
            </h2>
            <p className="mt-2 text-gray-600">開始追蹤您喜愛的漫畫</p>
          </div>

          {/* 錯誤訊息 */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* 表單 */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email 輸入 */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                電子郵件
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="your@email.com"
                disabled={isLoading}
              />
            </div>

            {/* 密碼輸入 */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                密碼
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="••••••••"
                disabled={isLoading}
              />
            </div>

            {/* 登入按鈕 */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '登入中...' : '登入'}
            </button>

            {/* 測試帳號提示 */}
            {/* <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 font-medium mb-2">
                測試帳號
              </p>
              <p className="text-xs text-blue-600">
                Email: test@email.com<br />
                密碼: permission
              </p>
              <button
                type="button"
                onClick={() => {
                  setEmail('test@email.com')
                  setPassword('permission')
                }}
                className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline"
                disabled={isLoading}
              >
                一鍵填入測試帳號
              </button>
            </div> */}
          </form>

          {/* 註冊連結 */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              還沒有帳號？{' '}
              <Link
                to={ROUTES.SIGNUP}
                className="font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
              >
                立即註冊
              </Link>
            </p>
          </div>
        </div>

        {/* 返回首頁連結 */}
        <div className="text-center mt-4">
          <Link
            to={ROUTES.HOME}
            className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← 返回首頁
          </Link>
        </div>
      </div>
    </div>
  )
}

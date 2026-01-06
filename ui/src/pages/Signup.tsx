import { useState, FormEvent, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { signUp } from '@/lib/allauth'
import { useAuth } from '@/contexts/AuthContext'
import { ROUTES } from '@/constants/routes'

export const Signup = () => {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const [email, setEmail] = useState('')
  const [password1, setPassword1] = useState('')
  const [password2, setPassword2] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  // 如果已登入，重定向到首頁（使用 useEffect 避免渲染期間的副作用）
  useEffect(() => {
    if (isAuthenticated) {
      navigate(ROUTES.HOME, { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')

    // 前端驗證
    if (password1 !== password2) {
      setError('兩次輸入的密碼不一致')
      return
    }

    if (password1.length < 8) {
      setError('密碼長度至少需要 8 個字元')
      return
    }

    setIsLoading(true)

    try {
      const result = await signUp(email, password1, password2)

      if (result.status === 200) {
        // 註冊成功，Custom Event 會自動更新 AuthContext
        navigate(ROUTES.HOME)
      } else {
        // 顯示錯誤訊息
        const errorMessage = result.errors?.[0]?.message || '註冊失敗'
        setError(errorMessage)
      }
    } catch (err: unknown) {
      console.error('Signup error:', err)
      setError('註冊失敗，請稍後再試')
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
              註冊 ComicChase
            </h2>
            <p className="mt-2 text-gray-600">加入我們，開始追蹤漫畫</p>
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
                htmlFor="password1"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                密碼
              </label>
              <input
                id="password1"
                name="password1"
                type="password"
                required
                value={password1}
                onChange={e => setPassword1(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="••••••••"
                disabled={isLoading}
              />
              <p className="mt-1 text-xs text-gray-500">至少 8 個字元</p>
            </div>

            {/* 確認密碼輸入 */}
            <div>
              <label
                htmlFor="password2"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                確認密碼
              </label>
              <input
                id="password2"
                name="password2"
                type="password"
                required
                value={password2}
                onChange={e => setPassword2(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                placeholder="••••••••"
                disabled={isLoading}
              />
            </div>

            {/* 註冊按鈕 */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-4 rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '註冊中...' : '註冊'}
            </button>
          </form>

          {/* 登入連結 */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              已經有帳號了？{' '}
              <Link
                to={ROUTES.LOGIN}
                className="font-medium text-indigo-600 hover:text-indigo-700 transition-colors"
              >
                立即登入
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

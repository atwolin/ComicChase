import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '@/api/client'
import { Error } from '@/components/Error'

// 登錄頁面
export const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  // 處理表單提交
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await authApi.login({ username, password })
      navigate('/collections')
    } catch (err: any) {
      setError(err.response?.data?.detail || '登錄失敗，請檢查使用者名稱和密碼')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">登錄</h1>
            <p className="text-gray-600">歡迎回到 ComicChase</p>
          </div>

          {error && <Error message={error} />}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                使用者名稱
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="請輸入使用者名稱"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                密碼
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="請輸入密碼"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '登錄中...' : '登錄'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              還沒有帳號？{' '}
              <Link to="/register" className="text-indigo-600 hover:text-indigo-700 font-medium">
                立即註冊
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

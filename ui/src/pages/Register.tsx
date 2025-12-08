import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '@/api/client'

export const Register = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError('密碼與確認密碼不一致')
      return
    }

    if (password.length < 6) {
      setError('密碼長度至少需要6個字符')
      return
    }

    setIsLoading(true)

    try {
      await authApi.register({ username, password, email })
      // 註冊成功後自動登錄
      await authApi.login({ username, password })
      navigate('/collections')
    } catch (err: any) {
      console.error('註冊錯誤:', err)
      if (err.response) {
        // 服務器返回錯誤響應
        const errorData = err.response.data
        if (errorData?.error) {
          setError(errorData.error)
        } else if (errorData?.username) {
          // Django 驗證錯誤格式
          setError(Array.isArray(errorData.username) ? errorData.username[0] : errorData.username)
        } else if (errorData?.password) {
          setError(Array.isArray(errorData.password) ? errorData.password[0] : errorData.password)
        } else if (errorData?.email) {
          setError(Array.isArray(errorData.email) ? errorData.email[0] : errorData.email)
        } else if (errorData?.detail) {
          setError(errorData.detail)
        } else {
          setError(`註冊失敗: ${JSON.stringify(errorData)}`)
        }
      } else if (err.request) {
        // 請求已發出但沒有收到響應
        setError('無法連接到服務器，請確認後端服務是否運行')
      } else {
        // 其他錯誤
        setError(err.message || '註冊失敗，請稍後再試')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">註冊</h1>
            <p className="text-gray-600">創建您的 ComicChase 帳號</p>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                用戶名
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="請輸入用戶名"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                電子郵件（選填）
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="請輸入電子郵件"
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
                minLength={6}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="至少6個字符"
              />
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                確認密碼
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="請再次輸入密碼"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '註冊中...' : '註冊'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              已有帳號？{' '}
              <Link to="/login" className="text-indigo-600 hover:text-indigo-700 font-medium">
                立即登錄
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}


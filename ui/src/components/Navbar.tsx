import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useState, useRef, useEffect } from 'react'
import { logout } from '@/lib/allauth'
import { useAuth } from '@/contexts/AuthContext'
import { SearchBar } from '@/components/SearchBar'
import { ROUTES } from '@/constants/routes'

export const Navbar = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, isAuthenticated } = useAuth()
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // 判斷是否為首頁
  const isHomePage = location.pathname === ROUTES.HOME

  // 點擊外部關閉下拉選單
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = async () => {
    try {
      const result = await logout()
      setIsDropdownOpen(false)

      // 檢查是否有錯誤
      if (result.errors && result.errors.length > 0) {
        const errorMsg = result.errors[0].message
        console.error('登出失敗:', errorMsg)
        alert(`登出失敗：${errorMsg}`)
        return
      }

      // 登出成功，Custom Event 會自動更新 AuthContext
      navigate(ROUTES.HOME)
    } catch (error) {
      console.error('登出錯誤:', error)
      // 靜默失敗，不顯示錯誤（因為用戶可能已經登出）
    }
  }

  return (
    <nav className="bg-white/80 backdrop-blur-md shadow-md border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo */}
          <Link
            to={ROUTES.HOME}
            className="flex items-center gap-3 transition-transform duration-300 hover:scale-105 origin-left flex-shrink-0"
          >
            <img
              src="/logo.png"
              alt="ComicChase"
              className="h-14 w-auto object-contain"
              onError={e => {
                const target = e.target as HTMLImageElement
                target.style.display = 'none'
              }}
            />
            <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              ComicChase
            </span>
          </Link>

          {/* 搜尋框 - 只在非首頁顯示 */}
          {!isHomePage && (
            <div className="flex-1 max-w-md mx-4">
              <SearchBar navigateOnSearch={true} compact={true} />
            </div>
          )}

          {/* 右側選單 */}
          <div className="flex items-center gap-4">
            {isAuthenticated && user ? (
              /* 已登入：顯示使用者資訊與下拉選單 */
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-semibold">
                    {(
                      user.email?.[0] ||
                      user.display?.[0] ||
                      '?'
                    ).toUpperCase()}
                  </div>
                  <span className="text-gray-700 font-medium hidden sm:block">
                    {user.display || user.email}
                  </span>
                  <svg
                    className={`w-4 h-4 text-gray-600 transition-transform ${
                      isDropdownOpen ? 'rotate-180' : ''
                    }`}
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
                </button>

                {/* 下拉選單 */}
                {isDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-50">
                    <div className="px-4 py-3 border-b border-gray-100">
                      <p className="text-sm font-medium text-gray-900">
                        {user.display || '使用者'}
                      </p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                    </div>

                    <Link
                      to={ROUTES.MY_SUBSCRIPTIONS}
                      onClick={() => setIsDropdownOpen(false)}
                      className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                        />
                      </svg>
                      我的追蹤
                    </Link>

                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    >
                      登出
                    </button>
                  </div>
                )}
              </div>
            ) : (
              /* 未登入：顯示登入/註冊按鈕 */
              <div className="flex items-center gap-3">
                <Link
                  to={ROUTES.LOGIN}
                  className="px-4 py-2 text-gray-700 hover:text-indigo-600 font-medium transition-colors"
                >
                  登入
                </Link>
                <Link
                  to={ROUTES.SIGNUP}
                  className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg"
                >
                  註冊
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

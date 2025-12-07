import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { clsx } from 'clsx'
import { authApi } from '@/api/client'
import type { User } from '@/types'

// 導覽列元件
export const Navbar = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const checkAuth = async () => {
      const authenticated = authApi.isAuthenticated()
      setIsAuthenticated(authenticated)
      if (authenticated) {
        try {
          const userData = await authApi.getCurrentUser()
          setUser(userData)
        } catch {
          // Token可能已過期
          authApi.logout()
          setIsAuthenticated(false)
        }
      }
    }
    checkAuth()
  }, [location])

  const handleLogout = () => {
    authApi.logout()
    setIsAuthenticated(false)
    setUser(null)
    navigate('/')
  }

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  return (
    <nav className="bg-white/80 backdrop-blur-md shadow-md border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-3 transition-transform duration-300 hover:scale-105 origin-left"
          >
            <img
              src="/logo.png"
              alt="ComicChase"
              className="h-14 w-auto object-contain"
              onError={(e) => {
                const target = e.target as HTMLImageElement
                target.style.display = 'none'
              }}
            />
            {/* 文字 */}
            <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              ComicChase
            </span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {isAuthenticated && (
              <Link
                to="/collections"
                className={clsx(
                  'px-4 py-2 rounded-lg font-medium transition-all',
                  isActive('/collections')
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'text-gray-700 hover:bg-gray-100'
                )}
              >
                我的收藏
              </Link>
            )}
            {isAuthenticated ? (
              <div className="flex items-center gap-3 ml-2">
                <span className="text-sm text-gray-600">{user?.username}</span>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  登出
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors ml-2"
              >
                登錄
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

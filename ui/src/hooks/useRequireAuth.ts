/**
 * 需要認證的操作 Hook
 *
 * 用於需要登入才能執行的操作
 * 如果未登入，可以選擇自動導向登入頁或由調用者自行處理
 */

import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { ROUTES } from '@/constants/routes'

interface RequireAuthOptions {
  /**
   * 未登入時是否自動導向登入頁
   * - true: 自動導向登入頁
   * - false: 返回 false，由調用者處理
   * @default false
   */
  autoRedirect?: boolean
}

/**
 * 包裝需要認證的操作
 *
 * @example
 * ```tsx
 * // 返回 false，由調用者處理
 * const { requireAuth, isAuthenticated } = useRequireAuth()
 *
 * const handleAction = requireAuth(() => {
 *   // 這裡的代碼只有在登入時才會執行
 *   await someApiCall()
 * })
 *
 * // 自動導向登入頁
 * const handleAction = requireAuth(() => {...}, { autoRedirect: true })
 * ```
 */
export function useRequireAuth() {
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated, user } = useAuth()

  /**
   * 獲取登入 URL（帶 redirect 參數）
   */
  const getLoginUrl = (): string => {
    const currentPath = location.pathname
    return `${ROUTES.LOGIN}?redirect=${encodeURIComponent(currentPath)}`
  }

  /**
   * 導向登入頁
   */
  const navigateToLogin = (): void => {
    navigate(getLoginUrl())
  }

  /**
   * 包裝一個需要認證的函數
   * 如果未登入，根據 autoRedirect 選項決定行為
   */
  const requireAuth = <T extends (...args: unknown[]) => unknown>(
    fn: T,
    options: RequireAuthOptions = {}
  ): ((...args: Parameters<T>) => ReturnType<T> | false) => {
    const { autoRedirect = false } = options

    return (...args: Parameters<T>): ReturnType<T> | false => {
      if (!isAuthenticated) {
        if (autoRedirect) {
          // 自動導向登入頁
          navigateToLogin()
        }
        // 返回 false 表示未執行
        return false
      }

      // 已登入，執行原函數
      return fn(...args) as ReturnType<T>
    }
  }

  return {
    isAuthenticated,
    user,
    requireAuth,
    getLoginUrl,
    navigateToLogin,
  }
}

/**
 * 認證 Context
 *
 * 基於官方 django-allauth react-spa 範例
 * 使用 Custom Event 機制同步認證狀態
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react'
import { getAuth, getConfig, type AuthResponse, type User } from '@/lib/allauth'

// ============================================================
// 類型定義
// ============================================================

interface AuthContextType {
  auth: AuthResponse | undefined
  config: AuthResponse | undefined
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

// ============================================================
// Context 建立
// ============================================================

const AuthContext = createContext<AuthContextType | null>(null)

// ============================================================
// Loading 組件
// ============================================================

function Loading() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <p className="mt-4 text-gray-600">載入中...</p>
      </div>
    </div>
  )
}

function LoadingError() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center">
      <div className="text-center">
        <p className="text-red-600 text-lg">載入失敗，請重新整理頁面</p>
      </div>
    </div>
  )
}

// ============================================================
// Auth Provider
// ============================================================

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [auth, setAuth] = useState<AuthResponse | undefined>(undefined)
  const [config, setConfig] = useState<AuthResponse | undefined>(undefined)

  useEffect(() => {
    // 監聽認證狀態變更事件
    function onAuthChanged(e: Event) {
      const customEvent = e as CustomEvent<AuthResponse>
      setAuth(prevAuth => {
        if (typeof prevAuth === 'undefined') {
          console.log('認證狀態已載入')
        } else {
          console.log('認證狀態已更新')
        }
        return customEvent.detail
      })
    }

    // 註冊事件監聽器
    document.addEventListener('allauth.auth.change', onAuthChanged)

    // 初始化：獲取認證狀態和設定
    console.log('[AuthContext] 開始載入認證狀態...')
    getAuth()
      .then(data => {
        console.log('[AuthContext] 認證狀態載入成功:', data)
        setAuth(data)
      })
      .catch(e => {
        console.error('[AuthContext] 獲取認證狀態失敗:', e)
        setAuth({ status: 500 } as AuthResponse)
      })

    console.log('[AuthContext] 開始載入設定...')
    getConfig()
      .then(data => {
        console.log('[AuthContext] 設定載入成功:', data)
        setConfig(data)
      })
      .catch(e => {
        console.error('[AuthContext] 獲取設定失敗:', e)
      })

    // 清理函數
    return () => {
      document.removeEventListener('allauth.auth.change', onAuthChanged)
    }
  }, [])

  // 計算衍生狀態
  // 注意：只依賴 auth，不依賴 config（config 是可選的）
  const loading = typeof auth === 'undefined'
  const user = auth?.data?.user || null
  const isAuthenticated = auth?.meta?.is_authenticated || false

  const value: AuthContextType = {
    auth,
    config,
    user,
    isAuthenticated,
    isLoading: loading,
  }

  // 顯示載入狀態
  if (loading) {
    return (
      <AuthContext.Provider value={value}>
        <Loading />
      </AuthContext.Provider>
    )
  }

  // 顯示錯誤狀態
  if (auth && auth.status >= 500) {
    return (
      <AuthContext.Provider value={value}>
        <LoadingError />
      </AuthContext.Provider>
    )
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// ============================================================
// useAuth Hook
// ============================================================

/**
 * 使用認證 Context 的 Hook
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

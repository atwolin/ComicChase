/**
 * Django-allauth Headless API 封裝
 *
 * 基於官方 react-spa 範例實作
 * https://github.com/pennersr/django-allauth/tree/main/examples/react-spa
 */

import { getCSRFToken } from './django'

// ============================================================
// 類型定義
// ============================================================

export interface User {
  id: number
  email: string
  display: string
  username?: string
  has_usable_password: boolean
}

export interface AuthResponse {
  status: number
  data?: {
    user?: User
    methods?: unknown[]
  }
  meta?: {
    is_authenticated?: boolean
    session_token?: string
    access_token?: string
  }
  errors?: Array<{
    message: string
    code: string
    param?: string
  }>
}

// ============================================================
// 設定
// ============================================================

const BASE_URL = '/_allauth/browser/v1'
const ACCEPT_JSON = {
  accept: 'application/json',
}

// 使用 sessionStorage 儲存 token（更安全，關閉分頁後自動清除）
const tokenStorage = window.sessionStorage

/**
 * 獲取 Session Token
 */
export function getSessionToken(): string | null {
  return tokenStorage.getItem('sessionToken')
}

// ============================================================
// 核心請求函數
// ============================================================

/**
 * 統一的 API 請求函數
 * 自動處理 CSRF Token 和 Session Token
 */
async function request(
  method: string,
  path: string,
  data?: unknown,
  headers?: Record<string, string>
): Promise<AuthResponse> {
  const options: RequestInit = {
    method,
    headers: {
      ...ACCEPT_JSON,
      ...headers,
    },
    credentials: 'include', // 發送 cookies
  }

  // 添加 CSRF Token（除了 /config 端點）
  if (path !== '/config') {
    const csrfToken = getCSRFToken()
    options.headers = {
      ...options.headers,
      'X-CSRFToken': csrfToken,
    }
  }

  // 如果有 body 數據
  if (typeof data !== 'undefined') {
    options.body = JSON.stringify(data)
    options.headers = {
      ...options.headers,
      'Content-Type': 'application/json',
    }
  }

  const response = await fetch(BASE_URL + path, options)

  // 檢查是否為 HTML 錯誤頁面（Django 的 CSRF 錯誤會返回 HTML）
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('text/html')) {
    await response.text() // 消費 response body

    // 返回格式化的錯誤
    const result: AuthResponse = {
      status: response.status,
      errors: [
        {
          message:
            response.status === 403
              ? 'CSRF 驗證失敗，請重新登入'
              : `請求失敗 (${response.status})`,
          code: 'html_error',
        },
      ],
    }
    console.log(`[allauth] Response status: ${result.status}`)
    return result
  }

  const result: AuthResponse = await response.json()
  console.log(`[allauth] Response status: ${result.status}`)

  // 儲存 session token
  if (result.meta?.session_token) {
    tokenStorage.setItem('sessionToken', result.meta.session_token)
  }

  // 如果 session 過期，清除 token
  if (result.status === 410) {
    tokenStorage.removeItem('sessionToken')
  }

  // 如果認證狀態改變，觸發 Custom Event
  if (
    [401, 410].includes(result.status) ||
    (result.status === 200 && result.meta?.is_authenticated)
  ) {
    const event = new CustomEvent('allauth.auth.change', { detail: result })
    document.dispatchEvent(event)
  }

  return result
}

// ============================================================
// 認證 API
// ============================================================

/**
 * 登入
 */
export async function login(
  email: string,
  password: string
): Promise<AuthResponse> {
  return await request('POST', '/auth/login', { email, password })
}

/**
 * 註冊
 */
export async function signUp(
  email: string,
  password1: string,
  password2: string
): Promise<AuthResponse> {
  return await request('POST', '/auth/signup', { email, password1, password2 })
}

/**
 * 登出
 */
export async function logout(): Promise<AuthResponse> {
  return await request('DELETE', '/auth/session')
}

/**
 * 獲取當前認證狀態
 */
export async function getAuth(): Promise<AuthResponse> {
  return await request('GET', '/auth/session')
}

/**
 * 獲取設定
 */
export async function getConfig(): Promise<AuthResponse> {
  return await request('GET', '/config')
}

// ============================================================
// 帳號管理 API（未來擴展）
// ============================================================

/**
 * 修改密碼
 */
export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<AuthResponse> {
  return await request('POST', '/account/password/change', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

/**
 * 請求密碼重置
 */
export async function requestPasswordReset(
  email: string
): Promise<AuthResponse> {
  return await request('POST', '/auth/password/request', { email })
}

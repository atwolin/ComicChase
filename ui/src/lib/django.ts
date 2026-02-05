/**
 * Django 工具函數
 *
 * 處理 CSRF Token 等 Django 特定功能
 */

/**
 * 從 cookie 中讀取指定名稱的值
 */
export function getCookie(name: string): string {
  let cookieValue = ''
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      // 檢查這個 cookie 是否是我們要找的
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

/**
 * 獲取 Django CSRF Token
 * Django 會自動設置 csrftoken cookie
 */
export function getCSRFToken(): string {
  return getCookie('csrftoken')
}

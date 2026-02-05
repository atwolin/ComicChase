# 郵件通知系統重構與問題修復紀錄

此文件詳細記錄了「郵件通知」與「取消訂閱」功能的除錯過程、架構決策以及最終的實作細節。

## 1. Bug 修復：郵件通知開關狀態錯誤

**問題描述：**
在「我的追蹤」頁面中，即使後端設定為關閉，"郵件通知" 開關在重新整理頁面後仍會錯誤地顯示為 "開啟 (On)" 狀態。

**根本原因分析 (Root Cause Analysis)：**

1. **Session Cookie 遺失問題：** 前端 (`comicchase.site`) 與後端 (`api.comicchase.site`) 位於不同子網域。前端發出的 `fetch` 請求原本缺少 `credentials: 'include'` 設定，導致瀏覽器為了安全考量，沒有在跨網域請求中帶上 Session Cookie (`sessionid`)。
2. **API 回應與判讀失敗：** 由於沒有 Cookie，後端視為未登入請求。
    * *舊架構行為 (FBV + `@login_required`):* 後端回傳 **302 Redirect** (重導向至登入頁)。
    * *前端處理失效:* 前端的 `fetch` 收到 302 回應 (或重導向後的 HTML)，無法正確解析為預期的 JSON 資料。Hook (`useUserPreferences`) 因此進入錯誤狀態或使用預設值。
3. **UI預設邏輯掩蓋錯誤：** 在讀取失敗或發生錯誤時，UI 元件預設將開關顯示為 `true` (開啟)，導致用戶誤以為設定已開啟，但實際上根本沒讀到後端資料。

**解決方案：**

* **前端 (Frontend):** 重構 `useUserPreferences.ts`，改用專案統一的 `apiClient`。此 Client 已預先配置好 `withCredentials: true` 以及正確的 `apiBaseUrl`，確保請求會帶上 Cookie 並直連後端 API (繞過 Firebase Hosting 的重寫規則)。
* **後端 (Backend):** 將 API 架構遷移至 **Django REST Framework (DRF)**。現在當用戶未登入時，後端會回傳標準的 **401 Unauthorized** (JSON 格式)，而非 302 重導向。這讓前端能精確判斷登入狀態並做出正確反應 (例如導向登入頁)，不再猜測。

## 2. 架構變更：全面採用 Django REST Framework (DRF)

**決策：**
將 `accounts/views.py` 中的所有 View 從原生的 Django Function-Based Views (FBV) 重構為 **DRF Class-Based Views (`APIView`)**。

**原因與效益：**

1. **架構一致性 (Consistency):** 專案中原本的 `comic` App 已經全面採用 DRF (`ViewSet`, `Serializer`)。將 `accounts` 統一為 DRF 風格，能避免專案出現兩種截然不同的 API 寫法，降低維護成本。
2. **標準化回應 (Standardized Responses):** DRF 提供標準的 JSON 錯誤回應機制 (如 `401 Unauthorized` vs `302 Found`)，這對於 Headless (前後端分離) 架構至關重要。原生 View 容易回傳 HTML 或重導向，這對 SPA 前端非常不友善。
3. **權限與認證 (Authentication & Permission):** 利用 DRF 的 `permission_classes = [IsAuthenticated]`，我們能以聲明式的方式管理權限，確保 API 的安全性，並與 `django-allauth` 完美整合。
4. **資料驗證 (Serialization):** 引入 `UserPreferenceSerializer` 將資料驗證邏輯封裝起來，取代了原本容易出錯的手動 `json.loads` 和字典操作，提升了程式碼的健壯性。

## 3. 功能重構：Headless 取消訂閱流程

**決策：**
將「取消訂閱」功能從後端渲染的 HTML 頁面 (`unsubscribe_confirmation.html`) 遷移至 **前端 React 頁面 (`ui/src/pages/Unsubscribe.tsx`)**，後端僅提供 JSON API。

**原因與效益：**

1. **徹底的 Headless 架構:** 在 Headless 架構中，後端應專注於提供 **資料 (Data/JSON)**，而非 **畫面 (UI/HTML)**。舊有的實作強迫後端渲染 HTML 頁面，破壞了職責分離原則。
2. **使用者體驗 (UX):** 改由前端處理後，用戶點擊取消訂閱連結時仍停留在 SPA (單頁式應用) 環境中。這帶來了更流暢的轉場體驗 (無須整頁重新整理)，並能保持與網站一致的視覺風格。
3. **API 設計:** 後端現在提供清晰的 `UnsubscribeView` API：
    * `GET /api/accounts/unsubscribe/?token=...`: 驗證 Token 合法性並回傳用戶 Email (供前端顯示確認畫面)。
    * `POST /api/accounts/unsubscribe/`: 接收 Token 並執行實際的取消訂閱動作。

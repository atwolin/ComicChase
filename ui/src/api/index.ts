/**
 * API Client - 統一導出入口
 *
 * 此文件整合自動生成的 API Client (@hey-api/openapi-ts)
 * 並提供統一的導入路徑
 */

import { client } from './generated/client.gen'

// ============================================================
// 配置 API Client
// ============================================================

// 設置 baseUrl 為空字符串
// 因為自動生成的 API 已經包含完整路徑（如 /api/comics/series/）
// 如果設置為 '/api'，會導致重複：/api/api/comics/series/
client.setConfig({
  baseUrl: '',
})

// ============================================================
// 導出所有 API 函數和類型
// ============================================================

// 導出所有 API 函數（如 comicsSeriesList, comicsSeriesRetrieve 等）
export * from './generated/sdk.gen'

// 導出所有 TypeScript 類型
export * from './generated/types.gen'

// 導出 client 實例（供需要直接操作 client 的場景使用）
export { client }

# GCE 部署： Firebase Hosting 配置說明

## ⚠️ 重要：Firebase Hosting 的限制

Firebase Hosting 的 `run` rewrite 配置：

- ✅ **只能指向 Cloud Run 服務**（在同一個 GCP 專案中）
- ❌ **不能使用外部 URL** 或 GCE 服務器地址
- ❌ **`serviceId` 只接受 Cloud Run 服務名稱**，不接受完整 URL

### 錯誤示例（無法運作）

```json
{
  "rewrites": [{
    "source": "/api/**",
    "run": {
      "serviceId": "https://api.comicchase.site"  // ❌ 這不會運作！
    }
  }]
}
```

**為什麼？** Firebase Hosting 的 rewrites 機制只能與 Cloud Run 集成，無法代理到外部服務器（包括 GCE）。

---

## 正確方案：前端直接調用 GCE API（推薦）✅

由於 `gce.py` 已經配置了 CORS，前端可以直接調用 GCE API，無需 Firebase Hosting 代理。

### 步驟 1：建立環境變數文件

建立 `ui/.env.gce`:

```env
VITE_API_BASE_URL=https://api.comicchase.site
```

> **注意**: `.env.gce` 被 gitignore，請手動建立此文件

### 步驟 2：Firebase 配置（只處理靜態文件）

建立 `ui/firebase.gce.json`:

```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      }
    ]
  }
}
```

### 步驟 3：前端 API 配置

確保前端的 API 基礎 URL 指向 GCE：

```typescript
// ui/src/config.ts 或類似文件
const API_BASE_URL = import.meta.env.PROD
  ? 'https://api.comicchase.site'  // GCE 域名
  : 'http://localhost:8000';

export { API_BASE_URL };
```

### 步驟 4：確認 CORS 配置

確認 `app/src/config/settings/gce.py` 包含：

```python
CORS_ALLOWED_ORIGINS = [
    "https://comicchase.site",  # Firebase Hosting URL
]

CSRF_TRUSTED_ORIGINS = [
    "https://comicchase.site",
]

ALLOWED_HOSTS = [
    "comicchase.site",  # Firebase Hosting
    "api.comicchase.site",  # GCE 域名
]
```

### 步驟 5：部署

```bash
cd ui

# 建置前端（使用 GCE 配置）
npm run build:gce

# 部署到 Firebase Hosting
firebase deploy --only hosting --config firebase.gce.json
```

### 步驟 6：驗證

1. **訪問 Firebase Hosting**：`https://comicchase.site`
2. **打開瀏覽器開發者工具 → Network**
3. **觸發 API 請求**，確認請求直接發送到 `https://api.comicchase.site`
4. **檢查 Response Headers**：

   ```http
   access-control-allow-origin: https://comicchase.site
   access-control-allow-credentials: true
   ```

---

## 優點

- ✅ **配置簡單** - 不需要額外的代理服務
- ✅ **減少延遲** - 直接連接，無中間層
- ✅ **更易於調試** - 請求路徑清晰可見
- ✅ **降低成本** - 不需要額外的 Cloud Run 代理服務

---

## 替代方案（進階）

如果確實需要統一入口點，可以考慮：

### 方案 A：Cloud Load Balancer

1. 建立 GCP HTTP(S) Load Balancer
2. 配置 backend 指向 GCE Instance Group
3. 配置 URL maps 路由不同路徑到不同服務
4. Firebase Hosting 作為 CDN

**適合：**

- 需要複雜的流量控制
- 多個 backend 服務
- 需要在 Load Balancer 層面處理 SSL

### 方案 B：Cloud Run 代理服務

部署一個 Cloud Run 服務作為反向代理：

```javascript
// proxy-service/index.js
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

app.use('/api', createProxyMiddleware({
  target: 'https://api.comicchase.site',
  changeOrigin: true,
}));

const port = process.env.PORT || 8080;
app.listen(port);
```

然後在 Firebase 中指向這個 Cloud Run 服務：

```json
{
  "rewrites": [{
    "source": "/api/**",
    "run": {
      "serviceId": "proxy-service",
      "region": "us-central1"
    }
  }]
}
```

**缺點：**

- 額外的複雜性和成本
- 增加延遲
- 需要維護額外服務

---

## 總結

| 方案 | 複雜度 | 成本 | 延遲 | 推薦度 |
| ------ | -------- | ------ | ------ | -------- |
| 直接 API 調用 + CORS | 低 | 低 | 最低 | ⭐⭐⭐⭐⭐ |
| Cloud Load Balancer | 高 | 中 | 低 | ⭐⭐⭐ |
| Cloud Run 代理 | 中 | 中 | 中 | ⭐⭐ |

**推薦：** 使用**直接 API 調用 + CORS** 方案，配置最簡單且性能最好。

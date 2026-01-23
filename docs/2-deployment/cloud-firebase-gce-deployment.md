# Firebase Hosting + GCE 部署架構

## 📋 文件目的

本文件說明如何將 ComicChase 專案部署為：

- **Frontend**: Firebase Hosting (全球 CDN)
- **Backend**: Google Compute Engine (VM)

採用前後端分離架構，結合 Firebase 的 CDN 優勢和 GCE 的靈活性。

---

> **⚠️ 重要更新（2026-01）**
>
> **Firebase Hosting 無法直接代理到 GCE！** 本文檔中 Phase 2 的部分配置示例已過時並且無法運作。
>
> **正確方案**：前端直接調用 GCE API + CORS 配置
>
> **👉 請參閱最新的配置指南：[Firebase + GCE 配置完整指南](./firebase-gce-config-guide.md)**
>
> 該指南包含：
>
> - Firebase Hosting 限制的詳細說明
> - 正確的 CORS 配置步驟
> - 完整的部署流程
> - 替代方案比較

---

## 🏗️ 架構概覽

### **部署架構圖**

```text
┌─────────────────────────────────────────────────────────────┐
│                        使用者請求                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Firebase Hosting (CDN)      │
        │   https://comicchase.web.app  │
        └───────────┬───────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
    ┌─────────┐         ┌──────────────┐
    │ Static  │         │ /api/** →   │
    │ Files   │         │ Rewrite to   │
    │ (React) │         │ GCE          │
    └─────────┘         └──────┬───────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  GCE VM (台灣)        │
                    │  Nginx Reverse Proxy │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │ Django   │  │ Celery   │  │ Postgres │
         │ (Gunicorn)  │ Worker   │  │ Database │
         └──────────┘  └──────────┘  └──────────┘
```

### **URL 設計**

| 請求路徑 | 處理方式 | 說明 |
| --------- | --------- | ------ |
| `https://comicchase.web.app/` | Firebase CDN | 首頁、React App |
| `https://comicchase.web.app/series/123` | Firebase CDN | 前端路由 |
| `https://comicchase.web.app/api/**` | Firebase Rewrite → GCE | API 請求 |
| `https://comicchase.web.app/admin/` | Firebase Rewrite → GCE | Django Admin |

---

## ✅ 優點分析

### **相較於純 GCE（Nginx 同時服務前後端）**

| 項目 | 純 GCE | Firebase + GCE | 優勢 |
| ------ | -------- | --------------- | ------ |
| **全球 CDN** | ❌ 單點台灣 | ✅ 全球 CDN | 海外使用者快 |
| **SSL 管理** | ⚠️ 手動 Certbot | ✅ 自動更新 | 省時省力 |
| **前端部署** | ⚠️ 需重建 Docker | ✅ `firebase deploy` 即時 | 快速部署 |
| **擴展性** | ⚠️ VM 資源限制 | ✅ 前端無限擴展 | 流量大時優勢 |
| **成本** | ✅ 單一 VM 費用 | ⚠️ VM + Firebase* | Firebase 有免費額度 |
| **架構複雜度** | ✅ 簡單 | ⚠️ 中等 | - |

*Firebase Hosting 免費額度：10GB 儲存 + 360MB/day 傳輸，小型專案足夠

---

## 🔧 實作內容

### Phase 1: 修改 Django Settings (gce.py)

#### **檔案：`app/src/config/settings/gce.py`**

```python
# app/src/config/settings/gce.py
from .base import *

# ============================================================
# GCE Production Settings (Firebase Frontend)
# ============================================================

# 繼承 base.py 的所有安全設定（Secure by Default）
# - DEBUG = False
# - SECURE_SSL_REDIRECT = True
# - CSRF_COOKIE_SECURE = True
# - SESSION_COOKIE_SECURE = True
# - SECURE_HSTS_* = True

# ============================================================
# Security Settings
# ============================================================

# Nginx 反向代理設定（必須）
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# SECRET_KEY - 必須透過環境變數提供
SECRET_KEY = env("SECRET_KEY")

# 管理員通知
ADMINS = [("atwolin", "tzhuchien@nlplab.cc")]

# ============================================================
# Host Configuration
# ============================================================

# 允許的 hosts：Firebase Hosting domain
ALLOWED_HOSTS = [
    "comicchase.web.app",           # Firebase Hosting
    "comicchase.firebaseapp.com",   # Firebase 預設域名
    ".comicchase.com.tw",           # 如果有自訂 domain
]

# ============================================================
# CORS & CSRF Settings
# ============================================================

# Firebase Hosting 使用 rewrite 功能，瀏覽器視為同域請求
# 但 Backend 會收到來自 Firebase 的請求，需要設定 CSRF_TRUSTED_ORIGINS

CSRF_TRUSTED_ORIGINS = [
    "https://comicchase.web.app",
    "https://comicchase.firebaseapp.com",
]

# 如果有自訂 domain
# CSRF_TRUSTED_ORIGINS += ["https://comicchase.com.tw"]

# 雖然是同域，但建議保留 CORS 設定（防禦性編程）
CORS_ALLOWED_ORIGINS = [
    "https://comicchase.web.app",
    "https://comicchase.firebaseapp.com",
]

CORS_ALLOW_CREDENTIALS = True  # 繼承自 base.py

# ============================================================
# Database Settings
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("DB_HOST", default="db"),  # Docker Compose 內部網路
        "PORT": env("DB_PORT", default=5432),
    }
}

# ============================================================
# Celery Settings
# ============================================================

# 繼承 base.py 的 Celery 設定
# CELERY_BROKER_URL 等已在 base.py 設定

# GCE 使用 RabbitMQ（透過環境變數設定）
# CELERY_BROKER_URL = amqp://guest:guest@rabbitmq:5672//

# ============================================================
# Static Files
# ============================================================

# Django static files（CSS/JS/Images）由 Nginx 提供
# React build files 由 Firebase Hosting 提供
# 所以這裡只需設定 Django 的 static files

STATIC_URL = "/django-static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ============================================================
# Logging (Optional)
# ============================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
```

---

### Phase 2: Firebase Hosting 配置

#### ⚠️ 重要限制說明

**Firebase Hosting 無法直接代理到 GCE！**

Firebase Hosting 的 `run` rewrite 配置：

- ✅ **只能指向 Cloud Run 服務**（同一 GCP 專案）
- ❌ **不能使用外部 URL** 或 GCE 地址
- ❌ **`serviceId` 只接受 Cloud Run 服務名稱**

**錯誤示例（無法運作）：**

```json
{
  "rewrites": [{
    "source": "/api/**",
    "run": {
      "serviceId": "https://api.comicchase.com.tw"  // ❌ 這不會運作！
    }
  }]
}
```

---

#### ✅ 正確方案：直接 API 調用 + CORS

對於 GCE 部署，推薦使用以下架構：

1. **Firebase Hosting** - 只託管前端靜態文件
2. **前端直接調用 GCE API** - `https://api.comicchase.com.tw`
3. **CORS 配置** - 在 `gce.py` 中已配置

**簡化配置：**

`ui/firebase.gce.json`:

```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
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

**前端 API 配置：**

```typescript
// ui/src/config.ts
const API_BASE_URL = import.meta.env.PROD
  ? 'https://api.comicchase.com.tw'
  : 'http://localhost:8000';
```

**部署：**

```bash
cd ui
npm run build
firebase deploy --only hosting --config firebase.gce.json
```

---

#### 📖 詳細配置指南

完整的配置步驟、CORS 設定、替代方案和驗證方法，請參考：

**👉 [Firebase + GCE 配置完整指南](./firebase-gce-config-guide.md)**

該指南包含：

- Firebase Hosting 限制的詳細說明
- 完整的 CORS 配置步驟
- 替代方案（Cloud Load Balancer、Cloud Run 代理）
- 驗證和調試方法

---

### Phase 3: 修改 GCE Nginx 設定

#### **檔案：`app/src/config/nginx/default.conf.template`**

GCE 的 Nginx **不再提供前端 static files**，只處理 API 和 Django Admin：

```nginx
# Upstream
upstream comicchase {
    server backend:8000;
}

# HTTP server (可選：如果不需要直接 HTTP 存取，可以移除)
server {
    listen       80;
    server_name  api.comicchase.com.tw comicchase.com.tw;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # 其他請求轉到 HTTPS（如果需要）
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen               443 ssl;
    http2                on;

    # SSL 憑證（使用 Certbot 自動生成）
    ssl_certificate      /code/app/ssl/fullchain.pem;
    ssl_certificate_key  /code/app/ssl/privkey.pem;

    server_name          api.comicchase.com.tw comicchase.com.tw;
    error_log            stderr warn;
    access_log           /dev/stdout main;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # API 流量
    location /api/ {
        # 不需要 rewrite（保留 /api 路徑）
        proxy_pass       http://comicchase;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_redirect   off;

        # Increase timeout for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Django Admin
    location /admin/ {
        proxy_pass       http://comicchase;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_redirect   off;
    }

    # Django static files
    location /django-static/ {
        alias /code/app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # DRF Spectacular (API docs)
    location /api/schema/ {
        proxy_pass       http://comicchase;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
        proxy_redirect   off;
    }
}
```

**重點變化：**

- ✅ 移除前端 React 相關的 location（由 Firebase 提供）
- ✅ 保留 `/api/`, `/admin/`, `/django-static/`
- ✅ 新增 health check endpoint
- ✅ `/api/` 不再 rewrite（保留完整路徑給 Django）

---

### Phase 4: 修改 Docker Compose 設定

#### **檔案：`docker-compose-gce.yaml`**

移除 `ui` service（前端由 Firebase 提供）：

```yaml
# docker-compose-gce.yaml

services:
  db:
    image: postgres:16.2
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

  rabbitmq:
    image: rabbitmq:3.13-management
    restart: unless-stopped
    ports:
      - "5672:5672"
      - "15672:15672"  # Management UI
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_USER:-guest}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASS:-guest}

  selenium:
    image: selenium/standalone-chrome:136.0
    restart: unless-stopped
    hostname: selenium
    ports:
      - "4444:4444"
    shm_size: 2gb  # 增加共享記憶體，避免 Chrome 崩潰

  backend:
    build:
      context: .
      args:
        USER_ID: ${UID:-1000}
        GROUP_ID: ${GID:-1000}
      dockerfile: ./app/Dockerfile.gce
    restart: unless-stopped
    volumes:
      - static_volume:/code/app/staticfiles
    expose:
      - "8000"
    env_file:
      - ./.env.gce
    depends_on:
      - db
      - rabbitmq
      - selenium

  celery:
    build:
      context: .
      args:
        USER_ID: ${UID:-1000}
        GROUP_ID: ${GID:-1000}
      dockerfile: ./app/Dockerfile.gce
    restart: unless-stopped
    command: celery -A config worker -l info -Q crawler
    env_file:
      - ./.env.gce
    depends_on:
      - db
      - rabbitmq
      - selenium

  nginx:
    image: nginx:1.28.0
    restart: unless-stopped
    ports:
      - "80:80"      # HTTP
      - "443:443"    # HTTPS
    volumes:
      - ./app/src/config/nginx:/etc/nginx/templates
      - ./app/src/ssl:/code/app/ssl:ro
      - static_volume:/code/app/staticfiles:ro
    depends_on:
      - backend

volumes:
  postgres_data:
  static_volume:
```

**重點變化：**

- ❌ 移除 `ui` service（前端由 Firebase 提供）
- ✅ 新增 `rabbitmq` service（Celery broker）
- ✅ 新增 `celery` worker service
- ✅ Nginx 直接暴露 80/443（作為 backend API server）

---

### Phase 5: 環境變數設定

#### **檔案：`.env.gce`（範例）**

建立 `.env.gce.example` 作為模板：

```bash
# .env.gce.example

# Django Settings
DJANGO_SETTINGS_MODULE=config.settings.gce
SECRET_KEY=your-production-secret-key-here-change-this

# Database
DB_HOST=db
DB_PORT=5432
POSTGRES_DB=comicchase_db
POSTGRES_PASSWORD=your-secure-password-here
POSTGRES_USER=comicchase_user

# Celery
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//

# Selenium
SELENIUM_HOST=selenium
SELENIUM_PORT=4444

# Optional: Email settings (for production)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-app-password

# Optional: Sentry (error tracking)
# SENTRY_DSN=https://your-sentry-dsn

# Optional: Override security settings (不建議)
# DEBUG=False
# DJANGO_SECURE_SSL_REDIRECT=True
```

**使用方式：**

```bash
# 複製範例檔案
cp .env.gce.example .env.gce

# 編輯實際的環境變數
vim .env.gce
```

---

## 🚀 部署步驟

### Step 1: 準備 GCE VM

#### 1.1 建立 GCE Instance

```bash
gcloud compute instances create comicchase-backend \
  --zone=asia-east1-b \
  --machine-type=e2-medium \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --tags=http-server,https-server
```

#### 1.2 設定防火牆規則

```bash
# 允許 HTTP/HTTPS 流量
gcloud compute firewall-rules create allow-http-https \
  --allow tcp:80,tcp:443 \
  --target-tags http-server,https-server
```

#### 1.3 SSH 連線到 VM

```bash
gcloud compute ssh comicchase-backend --zone=asia-east1-b
```

---

### Step 2: 設定 GCE 環境

#### 2.1 安裝 Docker

```bash
# 更新套件
sudo apt update
sudo apt upgrade -y

# 安裝 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 將當前用戶加入 docker 群組
sudo usermod -aG docker $USER

# 安裝 Docker Compose
sudo apt install docker-compose-plugin -y

# 重新登入以生效
exit
gcloud compute ssh comicchase-backend --zone=asia-east1-b
```

#### 2.2 安裝 Git

```bash
sudo apt install git -y
```

---

### Step 3: 部署 Backend

#### 3.1 Clone 專案

```bash
git clone https://github.com/your-username/ComicChase.git
cd ComicChase
```

#### 3.2 設定環境變數

```bash
# 複製範例檔案
cp .env.gce.example .env.gce

# 編輯環境變數
nano .env.gce
```

**必須修改的項目：**

- `SECRET_KEY`：產生新的 secret key
- `POSTGRES_PASSWORD`：資料庫密碼
- 其他敏感資訊

產生 SECRET_KEY：

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### 3.3 設定 SSL 憑證（Certbot）

```bash
# 安裝 Certbot
sudo apt install certbot -y

# 生成憑證（需要先將 domain 指向 VM IP）
sudo certbot certonly --standalone -d api.comicchase.com.tw

# 複製憑證到專案目錄
sudo mkdir -p app/src/ssl
sudo cp /etc/letsencrypt/live/api.comicchase.com.tw/fullchain.pem app/src/ssl/
sudo cp /etc/letsencrypt/live/api.comicchase.com.tw/privkey.pem app/src/ssl/
sudo chown -R $USER:$USER app/src/ssl
```

#### 3.4 設定自動更新憑證

Let's Encrypt 憑證有效期為 **90 天**，需要定期更新。Certbot 提供了自動化機制。

##### 方法 1：使用 systemd timer（推薦）✅

Certbot 安裝後會自動設定 systemd timer，**每天檢查兩次**憑證是否需要更新。

```bash
# 確認 timer 已啟用
sudo systemctl status certbot.timer

# 如果沒啟用，啟用它
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# 查看下次執行時間
sudo systemctl list-timers | grep certbot
```

**為什麼每天檢查？**

- ✅ **零成本檢查**：`certbot renew` 在憑證剩餘效期 > 30 天時會立即退出（不消耗資源）
- ✅ **即時更新**：一旦進入更新窗口（剩餘 ≤ 30 天），隔天就會自動更新
- ✅ **失敗重試**：如果某天更新失敗（網路問題），隔天會自動重試
- ✅ **Certbot 官方建議**：這是官方推薦的最佳實踐

**設定更新後的動作（deploy hook）：**

建立更新成功後才執行的腳本（**只在成功更新時才會執行，避免每天重啟**）：

```bash
# 建立 deploy hook 腳本
sudo nano /etc/letsencrypt/renewal-hooks/deploy/copy-to-docker.sh
```

加入以下內容：

```bash
#!/bin/bash
# 此腳本只在 certbot 成功更新憑證後才會執行

# 複製新憑證到 Docker 專案目錄
cp /etc/letsencrypt/live/api.comicchase.com.tw/fullchain.pem /home/$(logname)/ComicChase/app/src/ssl/
cp /etc/letsencrypt/live/api.comicchase.com.tw/privkey.pem /home/$(logname)/ComicChase/app/src/ssl/

# 重啟 Nginx 容器以載入新憑證
docker compose -f /home/$(logname)/ComicChase/docker-compose-gce.yaml restart nginx

# 記錄更新
echo "$(date): SSL certificate renewed and nginx restarted" >> /var/log/ssl-renewal.log
```

賦予執行權限：

```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/copy-to-docker.sh
```

測試憑證更新流程（dry-run）：

```bash
sudo certbot renew --dry-run
```

---

##### 方法 2：使用 cron job（備選

如果因為某些原因不想用 systemd timer，可以手動設定 cron job：

```bash
sudo crontab -e
```

加入以下內容（使用 `--deploy-hook` 參數，只在成功更新時才執行）：

```bash
# 每天凌晨 2 點檢查憑證（只在成功更新時才複製憑證並重啟 nginx）
0 2 * * * certbot renew --quiet --deploy-hook "cp /etc/letsencrypt/live/api.comicchase.com.tw/*.pem /home/your-username/ComicChase/app/src/ssl/ && docker compose -f /home/your-username/ComicChase/docker-compose-gce.yaml restart nginx"
```

**注意：** 記得將 `your-username` 替換為實際的用戶名。

---

**驗證自動更新設定：**

```bash
# 查看 certbot timer 狀態
sudo systemctl status certbot.timer

# 查看最近的執行記錄
sudo journalctl -u certbot.timer

# 手動測試更新流程（不會實際更新，只是測試）
sudo certbot renew --dry-run
```

#### 3.5 啟動服務

```bash
# 設定 UID/GID 環境變數
export UID=$(id -u)
export GID=$(id -g)

# 啟動所有服務
docker compose -f docker-compose-gce.yaml up -d --build

# 查看日誌
docker compose -f docker-compose-gce.yaml logs -f
```

#### 3.6 執行資料庫遷移

```bash
# 進入 backend container
docker compose -f docker-compose-gce.yaml exec backend bash

# 執行 migration
python manage.py migrate

# 建立 superuser
python manage.py createsuperuser

# 收集 static files
python manage.py collectstatic --noinput

# 退出 container
exit
```

---

### Step 4: 部署 Frontend (Firebase)

#### 4.1 在本地建置前端

```bash
cd ui

# 安裝依賴
npm install

# 建置 production build
npm run build
```

#### 4.2 部署到 Firebase

```bash
# 確保已登入 Firebase
firebase login

# 部署
firebase deploy --only hosting
```

#### 4.3 部署 Firebase Hosting

由於 Firebase Hosting 無法代理到 GCE，前端將直接調用 GCE API。
確保前端 API 配置指向 `https://api.comicchase.com.tw`，然後部署：

```bash
firebase deploy --only hosting
```

---

### Step 5: 驗證部署

#### 5.1 測試 Backend API

```bash
# 測試 health check
curl https://api.comicchase.com.tw/health

# 測試 API
curl https://api.comicchase.com.tw/api/comics/series/
```

#### 5.2 測試 Frontend

訪問：`https://comicchase.web.app`

確認：

- ✅ 首頁正常載入
- ✅ API 請求成功（檢查 Network tab）
- ✅ 登入功能正常

#### 5.3 測試 Django Admin

訪問：`https://comicchase.web.app/admin/`

確認可以登入 Django Admin

---

## 🔧 維護與監控

### 日誌查看

```bash
# 查看所有服務日誌
docker compose -f docker-compose-gce.yaml logs -f

# 查看特定服務
docker compose -f docker-compose-gce.yaml logs -f backend
docker compose -f docker-compose-gce.yaml logs -f celery
docker compose -f docker-compose-gce.yaml logs -f nginx
```

### 重啟服務

```bash
# 重啟所有服務
docker compose -f docker-compose-gce.yaml restart

# 重啟特定服務
docker compose -f docker-compose-gce.yaml restart backend
```

### 更新部署

```bash
# 拉取最新程式碼
git pull

# 重新建置並啟動
export UID=$(id -u) GID=$(id -g)
docker compose -f docker-compose-gce.yaml up -d --build

# 執行 migration（如果有）
docker compose -f docker-compose-gce.yaml exec backend python manage.py migrate
```

---

## 📊 成本估算

### GCE VM

| 項目 | 規格 | 月費用（USD）* |
| ------ | ------ | -------------- |
| VM Instance | e2-medium (2 vCPU, 4GB RAM) | ~$24.27 |
| Persistent Disk | 30GB SSD | ~$5.10 |
| External IP | 固定 IP | ~$2.88 |
| **總計** | | **~$32.25/月** |

*價格為台灣區域（asia-east1）估算，實際價格可能變動

### Firebase Hosting

| 項目 | 免費額度 | 超額費用 |
| ------ | --------- | --------- |
| 儲存空間 | 10 GB | $0.026/GB |
| 傳輸量 | 360 MB/day | $0.15/GB |

小型專案通常在免費額度內

### 總成本

約 **$32-40/月**（GCE + Firebase 超額費用）

---

## 🎯 優化建議

### 1. 使用 Cloud CDN

如果流量大，可以在 GCE 前加上 Cloud CDN：

```bash
gcloud compute backend-services create comicchase-backend \
  --global \
  --enable-cdn
```

### 2. 設定自動備份

```bash
# 每天備份資料庫
docker compose -f docker-compose-gce.yaml exec db pg_dump -U comicchase_user comicchase_db > backup_$(date +%Y%m%d).sql
```

### 3. 監控與告警

使用 Google Cloud Monitoring 設定告警：

- CPU 使用率 > 80%
- 記憶體使用率 > 80%
- Disk 使用率 > 80%

### 4. 設定 Log Rotation

```bash
# 限制 Docker 日誌大小
sudo nano /etc/docker/daemon.json
```

加入：

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

---

## 🔍 故障排除

### 問題 1: CORS 錯誤

**症狀：** Frontend 無法存取 API

**解決：**

```python
# gce.py
CORS_ALLOWED_ORIGINS = [
    "https://comicchase.web.app",
]
```

### 問題 2: CSRF 驗證失敗

**症狀：** POST 請求回傳 403

**解決：**

```python
# gce.py
CSRF_TRUSTED_ORIGINS = [
    "https://comicchase.web.app",
]
```

### 問題 3: SSL 憑證過期

**解決：**

```bash
# 手動更新
sudo certbot renew

# 複製新憑證
sudo cp /etc/letsencrypt/live/api.comicchase.com.tw/*.pem ~/ComicChase/app/src/ssl/

# 重啟 nginx
docker compose -f docker-compose-gce.yaml restart nginx
```

### 問題 4: Celery Worker 沒有執行任務

**檢查：**

```bash
# 查看 Celery logs
docker compose -f docker-compose-gce.yaml logs -f celery

# 檢查 RabbitMQ
docker compose -f docker-compose-gce.yaml exec rabbitmq rabbitmqctl list_queues
```

---

## 📚 參考資料

1. [Firebase Hosting Documentation](https://firebase.google.com/docs/hosting)
2. [Google Compute Engine Documentation](https://cloud.google.com/compute/docs)
3. [Certbot Documentation](https://certbot.eff.org/)
4. [Docker Compose Documentation](https://docs.docker.com/compose/)
5. [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)

---

**文件版本：** 1.0
**最後更新：** 2026-01-06
**作者：** ComicChase Development Team

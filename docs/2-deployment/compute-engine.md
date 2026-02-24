# Firebase Hosting + GCE VM 部署架構

## 📋 文件目的

本文件說明如何將 ComicChase 專案部署為：

- **Frontend**: Firebase Hosting（全球 CDN）
- **Backend + Celery**: Google Compute Engine VM（4GB RAM）

採用前後端分離架構，結合 Firebase 的 CDN 優勢和 GCE VM 的靈活性。
後端在 VM 上以 Docker Compose 運行所有服務，包含 Django、Celery workers、RabbitMQ、Selenium 等。

---

> [!IMPORTANT]
> **Firebase Hosting 無法直接代理到 GCE！**
> 前端透過 `VITE_API_BASE_URL` 直接呼叫 `https://api.comicchase.site`，無需 rewrite。

---

## 🏗️ 架構概覽

### **部署架構圖**

```text
                          使用者請求
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
  ┌──────────────────────┐    ┌──────────────────────────────────────────┐
  │  Firebase Hosting    │    │  GCE VM  (api.comicchase.site)          │
  │  (comicchase.site)   │    │  e2-medium / 24GB RAM                  │
  │  Static React App    │    │                                        │
  └──────────────────────┘    │  ┌────────────────────────────────────┐ │
    前端直接呼叫 API ──────────►  │  Nginx (128m) - SSL + Reverse Proxy│ │
    (VITE_API_BASE_URL)       │  └──────────────┬─────────────────────┘ │
                              │                 │                       │
                              │  ┌──────────────┼──────────────┐       │
                              │  ▼              ▼              ▼       │
                              │  ┌──────────┐ ┌──────────┐ ┌────────┐ │
                              │  │ Backend  │ │ Postgres │ │Rabbit- │ │
                              │  │ Gunicorn │ │   (1g)   │ │MQ      │ │
                              │  │  (512m)  │ └──────────┘ │ (512m) │ │
                              │  └──────────┘              └────────┘ │
                              │                                       │
                              │  ┌──────────┐ ┌────────────┐ ┌─────┐ │
                              │  │ Celery   │ │ Celery-    │ │Beat │ │
                              │  │ Worker   │ │ Crawler    │ │256m │ │
                              │  │   (1g)   │ │    (2g)    │ └─────┘ │
                              │  └──────────┘ └────────────┘         │
                              │                                       │
                              │  ┌──────────┐                         │
                              │  │ Selenium │    Total: ~7.4GB        │
                              │  │   (2g)   │                         │
                              │  └──────────┘                         │
                              └───────────────────────────────────────┘
```

### **URL 設計**

| 請求路徑 | 處理方式 | 說明 |
| --------- | --------- | ------ |
| `https://comicchase.site/` | Firebase CDN | 首頁、React App |
| `https://comicchase.site/series/123` | Firebase CDN | 前端路由（SPA） |
| `https://api.comicchase.site/api/**` | VM Nginx → Django | API 請求（前端直接呼叫） |
| `https://api.comicchase.site/admin/` | VM Nginx → Django | Django Admin |

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

### Phase 1: Django Settings (vm.py)

#### **檔案：`app/src/config/settings/vm.py`**

---

### Phase 2: Firebase Hosting 配置

#### ⚠️ 重要限制說明

**Firebase Hosting 無法直接代理到 GCE！**

Firebase Hosting 的 `run` rewrite 配置：

- ✅ **只能指向 Cloud Run 服務**（同一 GCP 專案）
- ❌ **不能使用外部 URL** 或 GCE 地址

---

#### ✅ 正確方案：使用兩份 Firebase 設定檔切換部署目標

由於 GCE 的前端透過 `VITE_API_BASE_URL` 直接呼叫 `https://api.comicchase.site`（完整 URL），瀏覽器請求**不會**經過 Firebase Hosting，因此 Cloud Run rewrites 不會被觸發。

兩份設定檔並存，用 `--config` 切換：

| 設定檔 | 用途 | 部署指令 |
|---|---|---|
| `firebase.json` | Cloud Run（現有，不動） | `firebase deploy --only hosting` |
| `firebase.vm.json` | GCE VM（新增） | `firebase deploy --only hosting --config firebase.vm.json` |

---

**新增 `ui/firebase.vm.json`（GCE 專用，移除 Cloud Run rewrites）：**

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

**前端 API Base URL** 透過 `ui/.env.vm` 設定（已正確）：

```env
VITE_API_BASE_URL=https://api.comicchase.site
```

> [!NOTE]
> GCE 部署時也可以直接使用原有的 `firebase.json`（Cloud Run rewrites 不會被觸發），`firebase.vm.json` 只是為了讓設定更乾淨明確。

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
    server_name  api.comicchase.site comicchase.site;

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

    server_name          api.comicchase.site comicchase.site;
    error_log            stderr warn;
    access_log           /dev/stdout main;

    # Security headers
    add_header Content-Security-Policy "frame-ancestors 'self'" always;
    add_header X-Content-Type-Options "nosniff" always;

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

#### **檔案：`docker-compose-vm.yaml`**

移除 `ui` service（前端由 Firebase 提供）：

```yaml
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
    deploy:
      resources:
        limits:
          memory: 1g

  selenium:
    image: selenium/standalone-chromium:136.0
    restart: unless-stopped
    hostname: selenium
    ports:
      - "4444:4444"
    deploy:
      resources:
        limits:
          memory: 2g

  rabbitmq:
    image: rabbitmq:4.2-management
    restart: unless-stopped
    env_file:
      - ./.env.vm
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    deploy:
      resources:
        limits:
          memory: 512m

  backend:
    build:
      context: .
      args:
        USER_ID: ${UID}
        GROUP_ID: ${GID}
      dockerfile: ./app/Dockerfile.vm
    restart: unless-stopped
    volumes:
      - static_volume:/code/app/staticfiles
    expose:
      - "8000"
    env_file:
      - ./.env.vm
    depends_on:
      - db
      - rabbitmq
    deploy:
      resources:
        limits:
          memory: 512m

  celery:
    build:
      context: .
      args:
        USER_ID: ${UID}
        GID: ${GID}
      dockerfile: ./app/Dockerfile.vm
    entrypoint: [""]
    command: celery -A config worker -l INFO
    restart: unless-stopped
    env_file:
      - ./.env.vm
    depends_on:
      - backend
      - rabbitmq
    deploy:
      resources:
        limits:
          memory: 1g

  celery-crawler:
    build:
      context: .
      args:
        USER_ID: ${UID}
        GID: ${GID}
      dockerfile: ./app/Dockerfile.vm
    entrypoint: [""]
    command: celery -A config worker -Q crawler -l INFO
    restart: unless-stopped
    env_file:
      - ./.env.vm
    depends_on:
      - backend
      - rabbitmq
    deploy:
      resources:
        limits:
          memory: 2g

  celery-beat:
    build:
      context: .
      args:
        USER_ID: ${UID}
        GID: ${GID}
      dockerfile: ./app/Dockerfile.vm
    entrypoint: [""]
    command: celery -A config beat -l INFO --schedule=/home/docker/celerybeat-schedule
    restart: unless-stopped
    volumes:
      - celerybeat_data:/home/docker
    env_file:
      - ./.env.vm
    depends_on:
      - backend
      - rabbitmq
    deploy:
      resources:
        limits:
          memory: 256m

  nginx:
    image: nginx:1.28.0
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./app/src/config/nginx:/etc/nginx/templates
      - ./app/src/ssl:/code/app/ssl:ro
      - static_volume:/code/app/staticfiles:ro
    depends_on:
      - backend
    deploy:
      resources:
        limits:
          memory: 128m

volumes:
  postgres_data:
  static_volume:
  rabbitmq_data:
  celerybeat_data:
```

**服務與記憶體配置：**

| Service | Memory Limit | 說明 |
|---|---|---|
| `db` | 1g | PostgreSQL |
| `selenium` | 2g | Chromium 瀏覽器爬蟲 |
| `rabbitmq` | 512m | Celery message broker |
| `backend` | 512m | Django + Gunicorn |
| `celery` | 1g | 一般 task worker |
| `celery-crawler` | 2g | 爬蟲專用 worker |
| `celery-beat` | 256m | 排程器 |
| `nginx` | 128m | SSL + 反向代理 |
| **Total** | **~7.4GB** | 適合 24GB VM |

**與舊版的差異：**

- ❌ 移除 `ui` service（前端由 Firebase Hosting 提供）
- ✅ 新增 `rabbitmq`（Celery broker）
- ✅ 新增 `celery`、`celery-crawler`、`celery-beat`
- ✅ 所有服務加上 `deploy.resources.limits.memory`
- ✅ Nginx 直接暴露 `80:80` / `443:443`

---

### Phase 5: 環境變數設定

#### **檔案：`.env.vm`（範例）**

建立 `.env.vm.example` 作為模板：

```bash
# .env.vm.example

# Django Settings
DEBUG=False
DJANGO_ALLOWED_HOSTS=comicchase.site,api.comicchase.site
DJANGO_SETTINGS_MODULE=config.settings.vm
FRONTEND_URL=https://comicchase.site
SECRET_KEY=change-this-to-a-secure-random-key-in-production

# Database
DB_HOST=db
DB_PORT=5432
POSTGRES_DB=comicchase_db
POSTGRES_PASSWORD=change-this-secure-password
POSTGRES_USER=comicchase_user

# Celery + RabbitMQ
CELERY_BROKER_URL=amqp://admin:admin@rabbitmq:5672/comicchase_vhost
RABBITMQ_DEFAULT_USER=admin
RABBITMQ_DEFAULT_PASS=admin
RABBITMQ_DEFAULT_VHOST=comicchase_vhost

# Selenium
SELENIUM_HUB_URL=http://selenium:4444/wd/hub

# Email (AWS SES)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=ap-northeast-1
AWS_SES_REGION=ap-northeast-1
AWS_SES_REGION_ENDPOINT=email.ap-northeast-1.amazonaws.com
DEFAULT_FROM_EMAIL=your-email@example.com
EMAIL_BACKEND=django_ses.SESBackend
```

**使用方式：**

```bash
# 複製範例檔案
cp .env.vm.example .env.vm

# 編輯實際的環境變數
vim .env.vm
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
cp .env.vm.example .env.vm

# 編輯環境變數
nano .env.vm
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
sudo certbot certonly --standalone -d api.comicchase.site

# 複製憑證到專案目錄
sudo mkdir -p app/src/ssl
sudo cp /etc/letsencrypt/live/api.comicchase.site/fullchain.pem app/src/ssl/
sudo cp /etc/letsencrypt/live/api.comicchase.site/privkey.pem app/src/ssl/
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
cp /etc/letsencrypt/live/api.comicchase.site/fullchain.pem /home/$(logname)/ComicChase/app/src/ssl/
cp /etc/letsencrypt/live/api.comicchase.site/privkey.pem /home/$(logname)/ComicChase/app/src/ssl/

# 重啟 Nginx 容器以載入新憑證
docker compose -f /home/$(logname)/ComicChase/docker-compose-vm.yaml restart nginx

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

##### 方法 2：使用 cron job（備選）

如果因為某些原因不想用 systemd timer，可以手動設定 cron job：

```bash
sudo crontab -e
```

加入以下內容（使用 `--deploy-hook` 參數，只在成功更新時才執行）：

```bash
# 每天凌晨 2 點檢查憑證（只在成功更新時才複製憑證並重啟 nginx）
0 2 * * * certbot renew --quiet --deploy-hook "cp /etc/letsencrypt/live/api.comicchase.site/*.pem /home/your-username/ComicChase/app/src/ssl/ && docker compose -f /home/your-username/ComicChase/docker-compose-vm.yaml restart nginx"
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
docker compose -f docker-compose-vm.yaml up -d --build

# 查看日誌
docker compose -f docker-compose-vm.yaml logs -f
```

#### 3.6 執行資料庫遷移

> `entrypoint.vm.sh` 會自動執行 `migrate` 和 `collectstatic`，正常啟動後只需要建立 superuser：

```bash
# 建立 superuser
docker compose -f docker-compose-vm.yaml exec backend python manage.py createsuperuser
```

---

### Step 4: 部署 Frontend (Firebase)

#### 4.1 在本地建置前端

```bash
cd ui

# 安裝依賴
npm install

# 建置 GCE production build（使用 ui/.env.vm，VITE_API_BASE_URL=https://api.comicchase.site）
npm run build:vm
```

#### 4.2 部署到 Firebase Hosting

```bash
# 確保已登入 Firebase
firebase login

# 部署（使用 ui/firebase.json）
firebase deploy --only hosting
```

---

### Step 5: 驗證部署

#### 5.1 檢查所有 Container

```bash
# 確認所有 8 個 container 都在運行
docker ps

# 確認記憶體限制是否生效
docker stats --no-stream
```

#### 5.2 測試 Backend API

```bash
# 測試 health check
curl https://api.comicchase.site/health

# 測試 API
curl https://api.comicchase.site/api/comics/series/
```

#### 5.3 測試 Celery

```bash
# 查看 Celery worker 日誌
docker compose -f docker-compose-vm.yaml logs celery celery-crawler celery-beat

# 確認 RabbitMQ 可用
docker compose -f docker-compose-vm.yaml exec rabbitmq rabbitmqctl list_queues
```

#### 5.4 測試 Frontend

訪問：`https://comicchase.site`

確認：

- ✅ 首頁正常載入
- ✅ API 請求成功（Network tab 確認打到 `api.comicchase.site`）
- ✅ 登入功能正常

#### 5.5 測試 Django Admin

訪問：`https://api.comicchase.site/admin/`

---

## 🔧 維護與監控

### 日誌查看

```bash
# 查看所有服務日誌
docker compose -f docker-compose-vm.yaml logs -f

# 查看特定服務
docker compose -f docker-compose-vm.yaml logs -f backend
docker compose -f docker-compose-vm.yaml logs -f celery
docker compose -f docker-compose-vm.yaml logs -f nginx
```

### 重啟服務

```bash
# 重啟所有服務
docker compose -f docker-compose-vm.yaml restart

# 重啟特定服務
docker compose -f docker-compose-vm.yaml restart backend
```

### 更新部署

```bash
# 拉取最新程式碼
git pull

# 重新建置並啟動
export UID=$(id -u) GID=$(id -g)
docker compose -f docker-compose-vm.yaml up -d --build

# 執行 migration（如果有）
docker compose -f docker-compose-vm.yaml exec backend python manage.py migrate
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

> 服務記憶體分配總計 ~3.2GB，適合 4GB VM。若 Celery worker 經常 OOM，考慮升級到 e2-standard-2（8GB）。

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
docker compose -f docker-compose-vm.yaml exec db pg_dump -U comicchase_user comicchase_db > backup_$(date +%Y%m%d).sql
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
# vm.py
CORS_ALLOWED_ORIGINS = [
    "https://comicchase.site",
]
```

### 問題 2: CSRF 驗證失敗

**症狀：** POST 請求回傳 403

**解決：**

```python
# vm.py
CSRF_TRUSTED_ORIGINS = [
    "https://comicchase.site",
]
```

### 問題 3: SSL 憑證過期

**解決：**

```bash
# 手動更新
sudo certbot renew

# 複製新憑證
sudo cp /etc/letsencrypt/live/api.comicchase.site/*.pem ~/ComicChase/app/src/ssl/

# 重啟 nginx
docker compose -f docker-compose-vm.yaml restart nginx
```

### 問題 4: Celery Worker 沒有執行任務

**檢查：**

```bash
# 查看 Celery logs
docker compose -f docker-compose-vm.yaml logs -f celery

# 檢查 RabbitMQ
docker compose -f docker-compose-vm.yaml exec rabbitmq rabbitmqctl list_queues
```

---

## 📚 參考資料

1. [Firebase Hosting Documentation](https://firebase.google.com/docs/hosting)
2. [Google Compute Engine Documentation](https://cloud.google.com/compute/docs)
3. [Certbot Documentation](https://certbot.eff.org/)
4. [Docker Compose Documentation](https://docs.docker.com/compose/)
5. [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)

---

**文件版本：** 2.0
**最後更新：** 2026-02-21
**作者：** ComicChase Development Team

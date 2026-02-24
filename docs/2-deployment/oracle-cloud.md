# Firebase Hosting + Oracle Cloud VM 部署架構

## 📋 文件目的

本文件說明如何將 ComicChase 專案部署為：

- **Frontend**: Firebase Hosting（全球 CDN）
- **Backend + Celery**: Oracle Cloud VM（Always Free ARM Instance）

採用前後端分離架構，結合 Firebase 的 CDN 優勢和 Oracle Cloud Always Free 的免費 VM 資源。
後端在 VM 上以 Docker Compose 運行所有服務，包含 Django、Celery workers、RabbitMQ、Selenium 等。

---

> [!IMPORTANT]
> **Oracle Cloud Always Free ARM Instance 使用 aarch64 架構！**
> 所有 Docker image 必須支援 ARM64。主要影響：
>
> - `selenium/standalone-chrome` ❌ → 改用 `selenium/standalone-chromium` ✅
> - `python:3.12-slim`、`postgres:16.2`、`nginx`、`rabbitmq` 均原生支援 ARM64 ✅

---

## 🏗️ 架構概覽

### **部署架構圖**

```text
                          使用者請求
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
  ┌──────────────────────┐    ┌──────────────────────────────────────────┐
  │  Firebase Hosting    │    │  Oracle Cloud VM (api.comicchase.site)  │
  │  (comicchase.site)   │    │  VM.Standard.A1.Flex (ARM)             │
  │  Static React App    │    │  4 OCPU / 24GB RAM / 200GB Storage     │
  └──────────────────────┘    │                                        │
    前端直接呼叫 API ──────────►  │  ┌────────────────────────────────────┐ │
    (VITE_API_BASE_URL)       │  │  Nginx (128m) - SSL + Reverse Proxy│ │
                              │  └──────────────┬─────────────────────┘ │
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
                              │  │Chromium  │    (ARM64 / aarch64)    │
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

### **相較於 GCE 方案**

| 項目 | GCE (e2-medium) | Oracle Cloud Always Free | 優勢 |
| ------ | -------- | --------------- | ------ |
| **月費** | ~$32/月 | **$0/月** | 💰 完全免費 |
| **RAM** | 4GB | 24GB | 記憶體充裕 |
| **CPU** | 2 vCPU (x86) | 4 OCPU (ARM) | 更多核心 |
| **儲存** | 30GB SSD（付費） | 200GB（免費） | 儲存充足 |
| **架構** | x86_64 | aarch64 (ARM) | ⚠️ 需注意相容性 |
| **穩定性** | ✅ 穩定 | ⚠️ 偶有回收風險* | - |

*Always Free Instance 極少數情況下可能被回收，但實際上非常穩定。建議設定監控。

---

## 🔧 實作內容

### Phase 1: Django Settings

#### **檔案：`app/src/config/settings/vm.py`**

> [!NOTE]
> Django settings 檔案 (`vm.py`) **不需要修改**。
> `ALLOWED_HOSTS`、`CORS_ALLOWED_ORIGINS`、`CSRF_TRUSTED_ORIGINS` 都是以 domain name 設定，
> 與底層 VM 在哪個雲端無關。

```python
# vm.py — 以下設定在 Oracle Cloud 上完全相同
ALLOWED_HOSTS = [
    "comicchase.site",       # Firebase Hosting
    "api.comicchase.site",   # VM API domain
]

CORS_ALLOWED_ORIGINS = [
    "https://comicchase.site",
]

CSRF_TRUSTED_ORIGINS = [
    "https://comicchase.site",
]
```

---

### Phase 2: Firebase Hosting 配置

#### **與 GCE 方案完全相同**

Firebase Hosting 只提供靜態前端檔案，跟後端在哪裡無關。

使用 `firebase.vm.json`（移除 Cloud Run rewrites）部署：

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

前端環境變數透過 `ui/.env.vm` 設定：

```env
VITE_API_BASE_URL=https://api.comicchase.site
VITE_ALLAUTH_BASE_URL=https://api.comicchase.site/_allauth/browser/v1
```

> [!IMPORTANT]
> `VITE_ALLAUTH_BASE_URL` 必須指向 API server 的完整路徑，否則 auth 請求會打到 Firebase（前端 domain）而非後端。

---

### Phase 3: Nginx 設定

#### **與 GCE 方案相同**

`app/src/config/nginx/default.conf.template` **不需要修改**。

---

### Phase 4: Docker Compose 設定

#### **檔案：`docker-compose-vm.yaml`**

> [!WARNING]
> **唯一必要改動：** Selenium image 需改為 ARM64 相容版本。
> `selenium/standalone-chrome` → `selenium/standalone-chromium`

Docker Compose 的其他所有設定（記憶體限制、volume、env_file 等）不需要任何修改。

```diff
  selenium:
-   image: selenium/standalone-chrome:136.0
+   image: selenium/standalone-chromium:136.0
    restart: unless-stopped
    hostname: selenium
    ports:
      - "4444:4444"
```

**服務與記憶體配置：**

| Service | Memory Limit | ARM64 相容 | 說明 |
|---|---|---|---|
| `db` (postgres:16.2) | 1g | ✅ | PostgreSQL |
| `selenium` (standalone-**chromium**) | 2g | ✅ | 爬蟲瀏覽器（ARM 版） |
| `rabbitmq` (4.2-management) | 512m | ✅ | Celery message broker |
| `backend` (python:3.12-slim) | 512m | ✅ | Django + Gunicorn |
| `celery` | 1g | ✅ | 一般 task worker |
| `celery-crawler` | 2g | ✅ | 爬蟲專用 worker |
| `celery-beat` | 256m | ✅ | 排程器 |
| `nginx` (1.28.0) | 128m | ✅ | SSL + 反向代理 |
| **Total** | **~7.4GB** | | 24GB VM 綽綽有餘 |

---

### Phase 5: 環境變數設定

#### **與 GCE 方案完全相同**

使用同一份 `.env.vm`，所有環境變數不需要修改：

```bash
# .env.vm（範例）
DEBUG=False
DJANGO_ALLOWED_HOSTS=comicchase.site,api.comicchase.site
DJANGO_SETTINGS_MODULE=config.settings.vm
FRONTEND_URL=https://comicchase.site
SECRET_KEY=change-this-to-a-secure-random-key-in-production

DB_HOST=db
DB_PORT=5432
POSTGRES_DB=comicchase_db
POSTGRES_PASSWORD=change-this-secure-password
POSTGRES_USER=comicchase_user

CELERY_BROKER_URL=amqp://admin:admin@rabbitmq:5672/comicchase_vhost
RABBITMQ_DEFAULT_USER=admin
RABBITMQ_DEFAULT_PASS=admin
RABBITMQ_DEFAULT_VHOST=comicchase_vhost

SELENIUM_HUB_URL=http://selenium:4444/wd/hub

AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=ap-northeast-1
AWS_SES_REGION=ap-northeast-1
AWS_SES_REGION_ENDPOINT=email.ap-northeast-1.amazonaws.com
DEFAULT_FROM_EMAIL=your-email@example.com
EMAIL_BACKEND=django_ses.SESBackend
```

---

## 🚀 部署步驟

### Step 1: 準備 Oracle Cloud VM

#### 1.1 建立 OCI 帳號

1. 前往 [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) 註冊
2. 選擇 **Home Region**（建議選擇離台灣近的區域，如 `ap-tokyo-1` 或 `ap-osaka-1`）

> [!TIP]
> Home Region **一旦選定就無法更改**，請謹慎選擇。
> 如果主要用戶在台灣，建議選 **Japan East (Tokyo)** 或 **Japan Central (Osaka)**。

#### 1.2 建立 Always Free ARM VM

**透過 OCI Console（推薦）：**

1. 進入 **Compute → Instances → Create Instance**
2. 設定如下：

| 設定項目 | 值 |
|---------|---|
| **Name** | `comicchase-backend` |
| **Compartment** | 預設（root compartment） |
| **Image** | Ubuntu 24.04 (aarch64) |
| **Shape** | VM.Standard.A1.Flex |
| **OCPU** | 4 |
| **Memory** | 24 GB |
| **Boot Volume** | 100 GB（Always Free 最大 200GB，留彈性） |
| **SSH Key** | 上傳或貼上你的公鑰 |

**或透過 OCI CLI：**

```bash
# 建立 VM（需先設定 OCI CLI）
oci compute instance launch \
  --compartment-id <your-compartment-ocid> \
  --availability-domain <your-ad> \
  --shape VM.Standard.A1.Flex \
  --shape-config '{"ocpus": 4, "memoryInGBs": 24}' \
  --image-id <ubuntu-2404-aarch64-image-ocid> \
  --subnet-id <your-subnet-ocid> \
  --ssh-authorized-keys-file ~/.ssh/id_rsa.pub \
  --display-name comicchase-backend \
  --boot-volume-size-in-gbs 100
```

> [!IMPORTANT]
> **Always Free ARM Instance 可能出現「Out of capacity」錯誤。**
> 這表示該區域暫時沒有可用的 ARM 資源。解決方式：
>
> - 換個時間重試（通常凌晨成功率較高）
> - 使用自動化腳本持續重試
> - 選擇不同的 Availability Domain

#### 1.3 設定防火牆規則（Security List）

OCI 預設會封鎖除 SSH (22) 以外的 ingress 流量。需要開啟 HTTP (80) 和 HTTPS (443)：

**透過 OCI Console：**

1. 進入 **Networking → Virtual Cloud Networks → 選擇你的 VCN**
2. 點選 **Security Lists → Default Security List**
3. 點選 **Add Ingress Rules**，加入以下規則：

| Source CIDR | Protocol | Destination Port | 說明 |
|-------------|----------|------------------|------|
| `0.0.0.0/0` | TCP | 80 | HTTP |
| `0.0.0.0/0` | TCP | 443 | HTTPS |

> [!CAUTION]
> **OCI 有兩層防火牆！**
> 除了 Security List，VM 本身的 **iptables** 也需要設定。
> Ubuntu 映像檔預設會用 `iptables` 封鎖流量，即使 Security List 已開放。
> 請務必完成 Step 2.3 的 iptables 設定。

**或透過 OCI CLI：**

```bash
oci network security-list update \
  --security-list-id <your-security-list-ocid> \
  --ingress-security-rules '[
    {"source": "0.0.0.0/0", "protocol": "6", "tcpOptions": {"destinationPortRange": {"min": 80, "max": 80}}},
    {"source": "0.0.0.0/0", "protocol": "6", "tcpOptions": {"destinationPortRange": {"min": 443, "max": 443}}},
    {"source": "0.0.0.0/0", "protocol": "6", "tcpOptions": {"destinationPortRange": {"min": 22, "max": 22}}}
  ]'
```

#### 1.4 SSH 連線到 VM

```bash
# 使用建立時的 SSH 金鑰連線
ssh -i ~/.ssh/id_ed25519 ubuntu@<VM-PUBLIC-IP>
```

> [!NOTE]
> OCI Ubuntu image 預設用戶名是 `ubuntu`（不是 `opc`，那是 Oracle Linux 的預設）。

---

### Step 2: 設定 VM 環境

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
ssh -i ~/.ssh/id_rsa ubuntu@<VM-PUBLIC-IP>
```

#### 2.2 安裝 Git

```bash
sudo apt install git -y
```

#### 2.3 設定 iptables（OCI 專屬步驟）

> [!WARNING]
> **這是 OCI 與 GCE 最大的差異之一！**
> OCI Ubuntu image 預設的 iptables 規則會封鎖 80/443 流量，
> 即使 Security List 已開放。必須手動放行。

```bash
# 開放 HTTP (80) 和 HTTPS (443)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

# 儲存 iptables 規則（重啟後仍生效）
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
```

驗證規則是否生效：

```bash
sudo iptables -L INPUT -n --line-numbers
# 應該能看到 port 80 和 443 的 ACCEPT 規則
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

> [!NOTE]
> 如果 VM 沒有 Python/Django，可以用以下替代方式產生：
>
> ```bash
> openssl rand -base64 50
> ```

#### 3.3 修改 Selenium Image（ARM64 相容）

在 `docker-compose-vm.yaml` 中將 Selenium image 改為 Chromium 版本：

```bash
# 確認修改
sed -i 's/selenium\/standalone-chrome/selenium\/standalone-chromium/g' docker-compose-vm.yaml
```

#### 3.4 設定 SSL 憑證（Certbot）

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

#### 3.5 設定自動更新憑證

Let's Encrypt 憑證有效期為 **90 天**，需要定期更新。

##### 方法 1：使用 systemd timer（推薦）✅

Certbot 安裝後會自動設定 systemd timer，**每天檢查兩次**。

```bash
# 確認 timer 已啟用
sudo systemctl status certbot.timer

# 如果沒啟用
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

**設定更新後的動作（deploy hook）：**

```bash
# 建立 deploy hook 腳本
sudo nano /etc/letsencrypt/renewal-hooks/deploy/copy-to-docker.sh
```

加入：

```bash
#!/bin/bash
# 此腳本只在 certbot 成功更新憑證後才會執行

# 複製新憑證到 Docker 專案目錄
cp /etc/letsencrypt/live/api.comicchase.site/fullchain.pem /home/ubuntu/ComicChase/app/src/ssl/
cp /etc/letsencrypt/live/api.comicchase.site/privkey.pem /home/ubuntu/ComicChase/app/src/ssl/

# 重啟 Nginx 容器以載入新憑證
docker compose -f /home/ubuntu/ComicChase/docker-compose-vm.yaml restart nginx

# 記錄更新
echo "$(date): SSL certificate renewed and nginx restarted" >> /var/log/ssl-renewal.log
```

賦予執行權限並測試：

```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/copy-to-docker.sh
sudo certbot renew --dry-run
```

##### 方法 2：使用 cron job（備選）

```bash
sudo crontab -e
```

```bash
# 每天凌晨 2 點檢查憑證
0 2 * * * certbot renew --quiet --deploy-hook "cp /etc/letsencrypt/live/api.comicchase.site/*.pem /home/ubuntu/ComicChase/app/src/ssl/ && docker compose -f /home/ubuntu/ComicChase/docker-compose-vm.yaml restart nginx"
```

#### 3.6 啟動服務

```bash
# 設定 UID/GID 環境變數
export UID=$(id -u)
export GID=$(id -g)

# 啟動所有服務
docker compose -f docker-compose-vm.yaml up -d --build

# 查看日誌
docker compose -f docker-compose-vm.yaml logs -f
```

> [!NOTE]
> **首次 build 在 ARM VM 上可能較慢**（特別是 pip install），
> 因為部分 Python 套件可能需要從原始碼編譯。後續 rebuild 會快很多。

#### 3.7 執行資料庫遷移

> `entrypoint.vm.sh` 會自動執行 `migrate` 和 `collectstatic`，正常啟動後只需要建立 superuser：

```bash
# 建立 superuser
docker compose -f docker-compose-vm.yaml exec -it backend python manage.py createsuperuser
```

#### 3.8 從 Cloud SQL 搬移資料（如需要）

如果需要從 GCP Cloud SQL 搬移現有資料到 Oracle Cloud VM：

##### Step 1：在本地取得 Cloud SQL 連線資訊

```bash
# 查看 DATABASE_URL（存在 GCP Secret Manager）
gcloud secrets versions access latest --secret=application_settings
# 從輸出找到：
# DATABASE_URL="postgres://USER:PASSWORD@//cloudsql/PROJECT:REGION:INSTANCE/DB_NAME"
```

##### Step 2：用 Cloud SQL Auth Proxy 匯出

```bash
# 下載 Cloud SQL Auth Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.15.2/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy

# 啟動 proxy（在另一個 terminal）
./cloud-sql-proxy comicchase:us-central1:comic-instance --port 5433

# 匯出資料庫（-F c = custom 壓縮格式）
pg_dump -h 127.0.0.1 -p 5433 -U dj-user -d dj-database -F c -f cloud_sql_backup.dump
# 輸入密碼（從 DATABASE_URL 取得）
```

##### Step 3：傳到 Oracle VM 並還原

```bash
# 傳到 VM
scp -i ~/.ssh/id_ed25519 cloud_sql_backup.dump ubuntu@<VM-PUBLIC-IP>:~/

# SSH 到 VM
ssh -i ~/.ssh/id_ed25519 ubuntu@<VM-PUBLIC-IP>

# 複製進 db 容器
docker cp cloud_sql_backup.dump comicchase-db-1:/tmp/

# 還原資料
cd ~/ComicChase
docker compose -f docker-compose-vm.yaml exec db \
  pg_restore -U comicchase_user -d comicchase_db --clean --if-exists --no-owner /tmp/cloud_sql_backup.dump

# 重啟 backend
docker compose -f docker-compose-vm.yaml restart backend
```

> [!NOTE]
> **還原時可能出現的正常警告：**
>
> ```text
> pg_restore: error: could not execute query: ERROR: role "cloudsqlsuperuser" does not exist
> pg_restore: warning: errors ignored on restore: 1
> ```
>
> 這是 Cloud SQL 專有的 role，本地 PostgreSQL 沒有，**不影響資料還原**。

##### Step 4：驗證資料

```bash
# 確認資料表存在
docker compose -f docker-compose-vm.yaml exec db \
  psql -U comicchase_user -d comicchase_db -c "\dt"

# 確認資料筆數
docker compose -f docker-compose-vm.yaml exec db \
  psql -U comicchase_user -d comicchase_db -c "SELECT COUNT(*) FROM comic_series;"
```

> [!IMPORTANT]
> **pg_restore 參數說明：**
>
> - `--clean`：先刪除現有 tables 再還原
> - `--if-exists`：搭配 `--clean`，table 不存在時不報錯
> - `--no-owner`：忽略原本的 owner（Cloud SQL 和 VM 的用戶名不同）

---

### Step 4: DNS 設定

將 domain 的 A record 指向 Oracle Cloud VM 的 **Public IP**：

| 紀錄類型 | 名稱 | 值 | TTL |
|---------|------|---|-----|
| A | `api.comicchase.site` | `<Oracle VM Public IP>` | 300 |

> [!TIP]
> Oracle Cloud Always Free 提供的 Public IP 是**永久的**（只要 VM 存在就不會改變），
> 不需要像某些雲端一樣另外申請 Static IP。

---

### Step 5: 部署 Frontend (Firebase)

#### 5.1 在本地建置前端

```bash
cd ui

# 安裝依賴
npm install

# 建置 production build（使用 ui/.env.vm）
npm run build:vm
```

#### 5.2 部署到 Firebase Hosting

```bash
# 確保已登入 Firebase
firebase login

# 部署
firebase deploy --only hosting --config firebase.vm.json
```

---

### Step 6: 驗證部署

#### 6.1 檢查所有 Container

```bash
# 確認所有 container 都在運行
docker ps

# 確認記憶體使用
docker stats --no-stream
```

#### 6.2 測試 Backend API

```bash
# 測試 health check
curl https://api.comicchase.site/admin/health

# 測試 API
curl https://api.comicchase.site/api/comics/series/
```

#### 6.3 測試 Celery

```bash
# 查看 Celery worker 日誌
docker compose -f docker-compose-vm.yaml logs celery celery-crawler celery-beat

# 確認 RabbitMQ 可用
docker compose -f docker-compose-vm.yaml exec rabbitmq rabbitmqctl list_queues
```

#### 6.4 測試 Frontend

訪問：`https://comicchase.site`

確認：

- ✅ 首頁正常載入
- ✅ API 請求成功（Network tab 確認打到 `api.comicchase.site`）
- ✅ 登入功能正常

#### 6.5 測試 Django Admin

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

### Oracle Cloud VM

| 項目 | 規格 | 月費用（USD） |
| ------ | ------ | -------------- |
| VM Instance | VM.Standard.A1.Flex (4 OCPU, 24GB) | **$0** |
| Boot Volume | 100GB | **$0** |
| Public IP | 1 個 | **$0** |
| Outbound Traffic | 10 TB/月（免費額度） | **$0** |
| **總計** | | **$0/月** |

### Firebase Hosting

| 項目 | 免費額度 | 超額費用 |
| ------ | --------- | --------- |
| 儲存空間 | 10 GB | $0.026/GB |
| 傳輸量 | 360 MB/day | $0.15/GB |

小型專案通常在免費額度內。

### 總成本比較

| 方案 | 月費用 |
|------|--------|
| Cloud Run + Firebase | ~$15-30/月 |
| GCE + Firebase | ~$32-40/月 |
| **Oracle Cloud + Firebase** | **~$0/月** ✅ |

---

## 🎯 優化建議

### 1. 設定自動備份

```bash
# 每天備份資料庫
docker compose -f docker-compose-vm.yaml exec db pg_dump -U comicchase_user comicchase_db > backup_$(date +%Y%m%d).sql
```

建議搭配 cron job 自動化：

```bash
# 每天凌晨 3 點備份
0 3 * * * cd /home/ubuntu/ComicChase && docker compose -f docker-compose-vm.yaml exec -T db pg_dump -U comicchase_user comicchase_db > /home/ubuntu/backups/backup_$(date +\%Y\%m\%d).sql
```

### 2. 監控 VM

OCI 內建基本監控（Compute → Instance → Metrics），可監控：

- CPU 使用率
- 記憶體使用率
- 網路流量
- Disk I/O

建議搭配外部 uptime 監控服務（如 UptimeRobot 免費方案）確認服務可用性。

### 3. 設定 Log Rotation

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

重啟 Docker：

```bash
sudo systemctl restart docker
```

### 4. 設定 Swap（視需要）

雖然 24GB RAM 非常充裕，但可以加 swap 做為安全網：

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 永久啟用
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 🔍 故障排除

### 問題 1: 無法連線到 80/443

**可能原因（OCI 特有）：**

1. **Security List 未開放** → 檢查 VCN Security List
2. **iptables 未放行** → 執行 Step 2.3
3. **Nginx 未啟動** → `docker ps` 確認

```bash
# 驗證 iptables
sudo iptables -L INPUT -n --line-numbers | grep -E "(80|443)"

# 驗證 Security List（從 VM 內部測試）
curl -v http://localhost:80
```

### 問題 2: CORS 錯誤

**症狀：** Frontend 無法存取 API

**解決：** 確認 `vm.py` 中的設定：

```python
CORS_ALLOWED_ORIGINS = [
    "https://comicchase.site",
]
```

### 問題 3: CSRF 驗證失敗

**症狀：** POST 請求回傳 403

**解決：**

```python
CSRF_TRUSTED_ORIGINS = [
    "https://comicchase.site",
]
```

### 問題 4: SSL 憑證過期

**解決：**

```bash
# 手動更新
sudo certbot renew

# 複製新憑證
sudo cp /etc/letsencrypt/live/api.comicchase.site/*.pem ~/ComicChase/app/src/ssl/

# 重啟 nginx
docker compose -f docker-compose-vm.yaml restart nginx
```

### 問題 5: Docker build 在 ARM 上失敗

**症狀：** 某些 Python 套件安裝失敗

**解決：** ARM 平台可能需要額外的系統相依套件：

```bash
# 在 Dockerfile.vm 中加入（如果需要）
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
```

### 問題 6: Selenium Chromium 在 ARM 上不穩定

**解決：** 確認使用正確的 ARM image：

```bash
# 確認 image 架構
docker inspect selenium/standalone-chromium:136.0 | grep Architecture
# 應該顯示 "arm64"
```

### 問題 7: Always Free VM 被回收

**預防措施：**

- 確保 VM 有持續的 CPU 活動（Celery Beat 排程通常足夠）
- 設定外部監控（如 UptimeRobot）
- 定期備份資料庫

---

## 📋 GCE → Oracle Cloud 遷移摘要

只需要修改的項目清單：

| # | 項目 | 說明 |
|---|------|------|
| 1 | **VM 建立** | 使用 OCI Console 建立 ARM instance |
| 2 | **防火牆** | OCI Security List + iptables |
| 3 | **SSH** | `ssh -i <key> ubuntu@<ip>` |
| 4 | **DNS** | A record 指向新 VM IP |
| 5 | **Selenium image** | `standalone-chrome` → `standalone-chromium` |

**不需要修改的項目：**

- ✅ Django settings (`vm.py`)
- ✅ Nginx 設定
- ✅ Docker Compose（除 Selenium image）
- ✅ Dockerfile.vm
- ✅ Firebase Hosting 設定
- ✅ 環境變數 (`.env.vm`)
- ✅ 前端程式碼

---

## 📚 參考資料

1. [Oracle Cloud Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
2. [OCI Compute Instance Documentation](https://docs.oracle.com/en-us/iaas/Content/Compute/home.htm)
3. [OCI Security Lists](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securitylists.htm)
4. [Firebase Hosting Documentation](https://firebase.google.com/docs/hosting)
5. [Certbot Documentation](https://certbot.eff.org/)
6. [Docker Compose Documentation](https://docs.docker.com/compose/)
7. [Selenium Docker ARM64 Support](https://github.com/SeleniumHQ/docker-selenium#experimental-mult-arch-aarch64armv8arm64-images)

---

**文件版本：** 1.0
**最後更新：** 2026-02-24
**作者：** ComicChase Development Team

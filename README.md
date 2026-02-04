# ComicChase

<div align="center">
    <img src="./assets/logo_with_text.png" width="520" alt="ComicChase logo"></div>

<p align="center">
    <b>ComicChase - 一個台日漫畫追蹤系統。</b><br>
    用於追蹤日文原版與台版漫畫單行本的出版資訊。
</p>

<details open>
<summary><b>目錄</b></summary>

- [簡介](#簡介)
- [頁面展示](#頁面展示)
- [主要功能](#主要功能)
- [系統架構](#系統架構)
  - [ER Diagram](#er-diagram)
- [技術堆疊](#技術堆疊)
- [用於開發的安裝說明](#用於開發的安裝說明)
  - [專案結構](#專案結構)
  - [Prerequisites](#prerequisites)
  - [使用 Docker 進行安裝](#使用-docker-進行安裝)
  - [環境變數說明](#環境變數說明)

</details>

## 簡介

這是一個比較日文原版與台版漫畫的出版進度，讓漫畫愛好者可以得知台版漫畫跟原版的落差。

## 頁面展示

<table>
  <tr>
    <td align="center" width="50%">
      <img src="assets/home.png" alt="首頁" /><br />
      <b>首頁</b><br />
      <sub>下方推薦顯示最新出版的漫畫</sub>
    </td>
    <td align="center" width="50%">
      <img src="assets/series_list.png" alt="漫畫列表" /><br />
      <b>漫畫列表</b><br />
      <sub>顯示所有漫畫</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <img src="assets/series_detail.png" alt="漫畫詳情" /><br />
      <b>漫畫詳情</b><br />
      <sub>顯示漫畫的詳細資訊，包括日版和台版的出版進度</sub>
    </td>
    <td align="center" width="50%">
      <img src="assets/signup.png" alt="註冊頁面" /><br />
      <b>註冊頁面</b><br />
      <sub>建立新帳號</sub>
    </td>
  </tr>
  <tr>
    <td align="center" colspan="2">
      <img src="assets/my_subscriptions.png" alt="我的追蹤" /><br />
      <b>我的追蹤</b><br />
      <sub>登入後可將漫畫加入追蹤，點擊右上角使用者圖示即可查看追蹤清單</sub>
    </td>
  </tr>
</table>

## 主要功能

| 功能 | 說明 |
| ------ | ------ |
| 📚 **出版進度比較** | 同步顯示日版和台版單行本出版進度，快速掌握翻譯進度落差 |
| 📖 **特殊版本支援** | 支援特裝版、首刷限定版等特殊版本資訊 |
| 🔔 **漫畫追蹤** | 登入後可追蹤喜愛的漫畫系列，建立個人化追蹤清單 |
| 📧 **Email 通知** | 追蹤的漫畫有新集數出版時，自動發送 Email 通知 |
| 🔍 **搜尋功能** | 依漫畫標題或作者名稱快速搜尋 |

## 系統架構

![system_architecture](assets/system_architecture.png)

### ER Diagram

主要功能的資料庫 schema  \
![core_models](assets/schema_core.png)

使用者相關的資料庫 schema（來自 [django-allauth](https://github.com/pennersr/django-allauth)）\
![user_models](assets/schema_user.png)

## 技術堆疊

- **Frontend:** React 18, tailwindcss
- **Backend:** Django 5.2
- **Database:** PostgreSQL 16
- **Scraper:** Scrapy + Selenium
- **Container:** Docker
- **CI/CD**: Pre-commit hooks (Linting with ruff), GitHub Actions CI, Google Cloud Build
- **Deployment:** Google Cloud Run + Firebase Hosting

## 用於開發的安裝說明

### 專案結構

```tree
ComicChase/
├── app/                          # 後端應用程式
│   ├── src/
│   │   ├── accounts/             # Django app - 使用者帳號管理
│   │   ├── apis/                 # Django app - API 相關功能
│   │   ├── comic/                # Django app - 漫畫模型和 API
│   │   ├── comic_scrapers/       # Scrapy 爬蟲
│   │   ├── config/               # Django 設定
│   │   │   ├── settings/         # Django 環境設定
│   │   │   ├── gunicorn/         # Gunicorn 設定
│   │   │   └── nginx/            # Nginx 設定
│   │   ├── subscriptions/        # Django app - 訂閱功能
│   │   ├── templates/            # Django 模板
│   │   ├── static/               # 靜態檔案
│   │   ├── manage.py             # Django 管理腳本
│   │   ├── scrapy.cfg            # Scrapy 設定
│   │   ├── supervisord.conf      # Supervisor 設定
│   │   ├── entrypoint.sh         # Docker 進入點腳本
│   │   ├── entrypoint.gce.sh     # GCE 進入點腳本
│   │   ├── entrypoint.gcr.sh     # GCR 進入點腳本
│   │   ├── run_crawler.sh        # 爬蟲執行腳本
│   │   ├── run_email.sh          # Email 發送腳本
│   │   └── wait-for-it.sh        # 資料庫等待腳本
│   ├── Dockerfile                # 後端 Local Docker 設定
│   ├── Dockerfile.gce            # Google Compute Engine 部署 Docker 設定
│   ├── Dockerfile.gcr            # Google Cloud Run 部署 Docker 設定
│   ├── requirements.txt          # Python 依賴套件
│   └── requirements-gcr.txt      # GCR Python 依賴套件
├── ui/                           # 前端應用程式
│   ├── src/
│   │   ├── api/                  # API 客戶端
│   │   ├── components/           # React 元件
│   │   ├── config/               # 環境設定
│   │   ├── constants/            # 常數定義
│   │   ├── contexts/             # React Contexts
│   │   ├── hooks/                # 自訂 Hooks
│   │   ├── lib/                  # 工具函式庫
│   │   ├── pages/                # 頁面元件
│   │   ├── test/                 # 測試檔案
│   │   ├── types/                # TypeScript 型別定義
│   │   ├── App.tsx               # 主要應用程式元件
│   │   └── main.tsx              # 應用程式進入點
│   ├── Dockerfile                # 前端 Local Docker 設定
│   ├── Dockerfile.gce            # Google Compute Engine 部署 Docker 設定
│   ├── Dockerfile.prod           # Google Cloud Run Docker 設定
│   ├── firebase.json             # Firebase 設定
│   ├── vite.config.ts            # Vite 設定
│   ├── tailwind.config.js        # Tailwind CSS 設定
│   └── package.json              # Node.js 依賴套件
├── docs/                         # 文檔
│   ├── 1-development/            # 開發文檔
│   ├── 2-deployment/             # 部署文檔
│   └── 3-backend/                # 後端文檔
├── scripts/                      # 工具腳本
│   └── check_zombie_processes.sh
├── assets/                       # 專案資源（logo 等）
├── docker-compose.yml            # Docker 服務編排
├── docker-compose-gce.yaml       # GCE Docker 編排
├── docker-compose-gcr-test.yaml  # GCR 測試 Docker 編排
├── cloudmigrate.yaml             # GCR 遷移設定
├── Makefile                      # Make 指令
├── pyproject.toml                # Python 專案設定
├── pyrightconfig.json            # Pyright 設定
└── package.json                  # 根目錄 Node.js 設定
```

### Prerequisites

- Docker >= 28.5.2 & Docker Compose >= v2.39.2

### 使用 Docker 進行安裝

1. Clone 專案並安裝 linters

   ```bash
   git clone https://github.com/atwolin/ComicChase.git
   cd ComicChase
   pre-commit install
   ```

2. 設定環境變數

   1. 開發環境

      ```bash
      # 複製 .env.example 作為實際使用的 .env 檔案
      cp .env.example .env

      # 修改 .env 檔案裡的環境變數
      nano .env
      ```

   2. Google Compute Engine 部署

      ```bash
      # 修改 .env.gce 檔案裡的環境變數
      nano .env.gce
      ```

3. 啟動 Docker

   1. 啟動服務

      ```bash
      make rebuild
      ```

   2. 建立管理員帳號

      ```bash
      make manage cmd="createsuperuser"
      ```

可存取的微服務：

- Django Admin:: <http://localhost:8000/admin>
- Selenium Grid: <http://localhost:4444>
- Flower: <http://localhost:5555>
- RabbitMQ: <http://localhost:15672>
- UI: <http://localhost:3000>

### 環境變數說明

- `.env.example`:

```env
# 預設用於 Docker 的 UID/GID
GID=1000
UID=1000

# 用於開發環境的 Django 設定
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings.local
SECRET_KEY=your-secret-key-here

# PostgreSQL 資料庫設定
DB_HOST=db
DB_PORT=5432
POSTGRES_DB=your-db-name
POSTGRES_PASSWORD=your-db-password
POSTGRES_USER=your-db-user

# Email settings
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_DEFAULT_REGION=your-default-region
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_SES_REGION=your-ses-region
AWS_SES_REGION_ENDPOINT=your-ses-region-endpoint
DEFAULT_FROM_EMAIL=your-email@your-domain.com
EMAIL_BACKEND=django_ses.SESBackend

# Celery 設定
CELERY_BROKER_URL=amqp://admin:admin@rabbitmq:5672/staging_vhost

# RabbitMQ 設定
RABBITMQ_DEFAULT_PASS=your-broker-password
RABBITMQ_DEFAULT_USER=your-broker-user
RABBITMQ_DEFAULT_VHOST=staging_vhost
```

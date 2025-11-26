<div align="center">
    <img src="src/assets/logo-with-text.png" width="520" alt="comicChase logo"></div>

<p align="center">
    <b>ComicChase - 一個台日漫畫追蹤系統。</b><br>
    用於追蹤日文原版與台版漫畫單行本的出版資訊。
</p>

<details open>
<summary><b>目錄</b></summary>

- [簡介](#簡介)
- [Demo](#demo)
- [主要功能](#主要功能)
- [系統架構](#系統架構)
- [技術堆疊](#技術堆疊)
- [用於開發的安裝說明](#用於開發的安裝說明)
  - [專案結構](#專案結構)
  - [Prerequisites](#prerequisites)
  - [使用 Docker 進行安裝](#使用-docker-進行安裝)
  - [環境變數說明](#環境變數說明)

</details>

## 簡介

這是一個比較日文原版與台版漫畫的出版進度，讓漫畫愛好者可以得知台版漫畫跟原版的落差。

## Demo

## 主要功能

### 出版進度

- 同步顯示日版和台版單行本出版進度
- 各個單行本支援特殊版本（特裝版、首刷限定等）

## 系統架構

## 技術堆疊

- **Backend:** Django 5.2
- **Database:** PostgreSQL 16
- **Scraper:** Scrapy + Selenium
- **CI/CD**: Pre-commit hooks (Linting with ruff/pyright)
- **Container:** Docker

## 用於開發的安裝說明

### 專案結構

```tree
ComicChase/
├── src/
│   ├── comic/              # Django app - 漫畫模型和 API
│   ├── comic_scrapers/     # Scrapy 爬蟲
│   └── config/             # Django 設定
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Prerequisites

- Docker >= 28.5.2 & Docker Compose >= v2.39.2
- Python >= 3.12

### 使用 Docker 進行安裝

1. Clone 專案並安裝 Python dependencies

```bash
git clone https://github.com/atwolin/ComicChase.git
cd ComicChase
pre-commit install
```

2. 設定環境變數

```bash
# 建立 .env.example 檔案並寫入環境變數
cat > .env.example << EOF
SECRET_KEY=your-secret-key-here
DEBUG=True
POSTGRES_DB=comic_db
POSTGRES_USER=comic_user
POSTGRES_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
EOF

# 複製為實際使用的 .env 檔案
cp .env.example .env
```

3. 啟動 Docker

   > 啟動服務
   >
   > ```bash
   > docker compose up -d
   > ```
   >
   > 執行資料庫遷移
   >
   > ```bash
   > docker compose exec web python manage.py migrate
   > ```
   >
   > 建立管理員帳號
   >
   > ```bash
   > docker compose exec web python manage.py createsuperuser
   > ```

### 環境變數說明

- `.env.example`:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
POSTGRES_DB=comic_db
POSTGRES_USER=comic_user
POSTGRES_PASSWORD=your-password
DB_HOST=db
DB_PORT=5432
```

- `docker-compose.yaml`


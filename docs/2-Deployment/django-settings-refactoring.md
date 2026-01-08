# Django Settings 重構計畫

## 📋 文件目的

本文件說明 ComicChase 專案的 Django settings 重構計畫，採用「Secure by Default」最佳實踐，統一環境變數管理策略，並確保生產環境的安全性。

## 🎯 核心原則

### 1. Secure by Default（安全優先）

> 參考自 *Django for Professionals* by William S. Vincent:
>
> "This means default to a production value of False if no environment variable is present. If there is one available, DJANGO_DEBUG, then use that instead. This approach of defaulting to the most secure, production-only settings is more secure because if for some reason environment variables are not loading in properly, we don't want to the website to just use insecure local development variables."

**核心概念：**
- ✅ **預設使用最安全的 production 設定**（`DEBUG=False`, `HTTPS=True`）
- ✅ **需要時才透過環境變數放寬限制**（開發環境）
- ✅ **若環境變數載入失敗，系統會使用安全的預設值**（fail-safe）

### 2. DRY（Don't Repeat Yourself）

- 所有通用設定統一在 `base.py` 管理
- 各環境只覆寫必要的特定設定
- 避免在多個檔案重複相同的設定

### 3. 12-Factor App

- 配置透過環境變數管理
- 環境之間的差異最小化
- 清楚區分 build 和 config

---

## 🏗️ 目前架構分析

### 環境配置概覽

| 環境 | 檔案 | 用途 | 部署方式 |
|------|------|------|---------|
| **Development** | `local.py` | 本地開發 | Docker Compose（local） |
| **Production (Serverless)** | `gcr.py` | Cloud Run | Firebase Hosting + Cloud Run |
| **Production (VM)** | `gce.py` | Compute Engine | Nginx + Docker（傳統 VM） |

### 部署架構差異

#### **local.py（開發環境）**
```
Frontend: http://localhost:3000    (React dev server)
Backend:  http://localhost:8000    (Django dev server)
```
- ✅ 使用 HTTP（不需要 SSL）
- ✅ 跨域請求（需要 CORS 設定）
- ✅ DEBUG 模式
- ✅ 使用 Celery（RabbitMQ）

#### **gcr.py（Cloud Run）**
```
Frontend: https://comicchase.web.app/          (Firebase Hosting)
Backend:  https://comicchase.web.app/api/...  (Firebase proxy 到 Cloud Run)
```
- ✅ 使用 HTTPS
- ✅ Firebase 自動處理 proxy（同域，不需要 CORS）
- ✅ **不使用 Celery**（使用 Cloud Job 執行非同步任務）
- ✅ 使用 Cloud SQL + Cloud Storage

#### **gce.py（Compute Engine）**
```
Frontend: https://comicchase.web.app/          (Firebase Hosting)
Backend:  https://comicchase.web.app/api/...  (Firebase rewrite 到 GCE)
```
- ✅ 使用 HTTPS + Nginx 反向代理（僅後端）
- ✅ Firebase Hosting rewrite（同域請求）
- ✅ 使用 Celery（RabbitMQ）執行非同步任務
- ✅ 完整的 HSTS 安全設定
- ✅ 前端享有全球 CDN（Firebase）

---

## ⚠️ 目前的問題

### 1. **混用兩個環境變數套件**

```python
# base.py
from decouple import config  # ← python-decouple

# gcr.py
import environ               # ← django-environ
env = environ.Env()
```

**問題：**
- ❌ 功能重複，增加維護成本
- ❌ 無法統一使用 django-environ 的進階功能（如 `env.db()`）
- ❌ 容易產生混淆

### 2. **DEBUG 設定不一致**

```python
# base.py
# DEBUG = config("DEBUG", default=False, cast=bool)  # 被註解掉

# local.py
DEBUG = True  # 硬編碼

# gcr.py
DEBUG = env("DEBUG")  # 必須提供環境變數，否則報錯

# gce.py
DEBUG = False  # 硬編碼
```

**問題：**
- ❌ 沒有統一的真相來源
- ❌ gcr.py 若環境變數未設定會報錯（不是 fail-safe）
- ❌ 違反 Secure by Default 原則

### 3. **重複的設定項目**

```python
# base.py
SECRET_KEY = config("SECRET_KEY", default="django-insecure-...")
CORS_ALLOW_CREDENTIALS = True

# gcr.py
SECRET_KEY = env("SECRET_KEY")  # ← 重複
CORS_ALLOW_CREDENTIALS = True   # ← 重複

# gce.py
SECRET_KEY = config("SECRET_KEY")  # ← 重複
```

### 4. **缺少生產環境的安全設定**

gcr.py 缺少以下重要的安全設定：
- ❌ `CSRF_COOKIE_SECURE`
- ❌ `SESSION_COOKIE_SECURE`
- ❌ `SECURE_SSL_REDIRECT`
- ❌ `SECURE_PROXY_SSL_HEADER`
- ❌ `SECURE_HSTS_*` 設定

---

## ✅ 解決方案

### 原則：統一使用 django-environ + Secure by Default

#### **為什麼選擇 django-environ？**

| 特性 | python-decouple | django-environ | 決定 |
|------|----------------|----------------|------|
| **輕量級** | ✅ | ❌ | - |
| **Django 專用功能** | ❌ | ✅ `env.db()`, `env.cache()` | ✅ 需要 |
| **自動解析 URL** | ❌ 需要額外套件 | ✅ 內建 | ✅ gcr.py 需要 |
| **gcr.py 的 `APPLICATION_SETTINGS` 支援** | ❌ | ✅ | ✅ 必須 |
| **社群支援（Django）** | ⚠️ 中等 | ✅ 主流 | ✅ 更好 |

**結論：統一使用 `django-environ`**

---

## 📝 修改計畫

### Phase 1：統一環境變數套件

#### 1.1 移除 python-decouple 依賴

```bash
# 在 app/requirements.txt 中移除
# python-decouple
```

#### 1.2 確保 django-environ 已安裝

```bash
# 確認 app/requirements.txt 包含
django-environ>=0.11.2
```

### Phase 2：重構 base.py（統一真相來源）

#### 2.1 初始化 django-environ

```python
# app/src/config/settings/base.py
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 初始化 environ（設定 Secure by Default 預設值）
env = environ.Env(
    # Security Settings (Production-safe defaults)
    DEBUG=(bool, False),
    DJANGO_SECURE_SSL_REDIRECT=(bool, True),
    DJANGO_CSRF_COOKIE_SECURE=(bool, True),
    DJANGO_SESSION_COOKIE_SECURE=(bool, True),
    DJANGO_SECURE_HSTS_SECONDS=(int, 31536000),  # 1 year
    DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=(bool, True),
    DJANGO_SECURE_HSTS_PRELOAD=(bool, True),
)

# 讀取 .env 檔案（如果存在）
env.read_env(BASE_DIR / '.env')
```

#### 2.2 設定核心安全項目

```python
# ============================================================
# Security Settings (Secure by Default)
# ============================================================

# DEBUG - 預設 False（production-safe）
DEBUG = env('DEBUG')

# Secret Key - 提供開發用預設值
SECRET_KEY = env(
    'SECRET_KEY',
    default='django-insecure-test-key-for-development-only'
)

# HTTPS/SSL Settings
SECURE_SSL_REDIRECT = env('DJANGO_SECURE_SSL_REDIRECT')
CSRF_COOKIE_SECURE = env('DJANGO_CSRF_COOKIE_SECURE')
SESSION_COOKIE_SECURE = env('DJANGO_SESSION_COOKIE_SECURE')

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = env('DJANGO_SECURE_HSTS_SECONDS')
SECURE_HSTS_INCLUDE_SUBDOMAINS = env('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS')
SECURE_HSTS_PRELOAD = env('DJANGO_SECURE_HSTS_PRELOAD')

# Note: SECURE_PROXY_SSL_HEADER 需在各環境設定（gcr.py, gce.py）
# 因為只有使用反向代理的環境才需要
```

#### 2.3 設定開發環境的 CORS（本地需要）

```python
# ============================================================
# CORS Settings (for local development)
# ============================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True
```

**說明：**
- 本地開發時 frontend (3000) 和 backend (8000) 是不同 port，需要 CORS
- gcr.py 和 gce.py 都使用 proxy，會覆寫這些設定

#### 2.4 保留 Celery 設定

```python
# ============================================================
# Celery Configuration
# ============================================================
# Note: gcr.py 不使用 Celery（使用 Cloud Job），但這些設定不會影響其運作

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='amqp://')
CELERY_RESULT_BACKEND = 'django-db'
# ... 其他 Celery 設定保持不變
```

**說明：**
- local.py 和 gce.py 需要 Celery
- gcr.py 不使用 Celery，但這些設定不會造成問題（Django 不會自動啟動 Celery）

### Phase 3：重構 local.py（開發環境）

```python
# app/src/config/settings/local.py
from .base import *
import sys

# ============================================================
# Development Settings - Override for Local Development
# ============================================================

# 開啟 DEBUG 模式
DEBUG = True

# 關閉所有 HTTPS 安全設定（本地用 HTTP）
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# 資料庫設定（保持不變）
if "test" in sys.argv or "pytest" in sys.modules:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", default="comic_db"),
            "USER": env("POSTGRES_USER", default="comic_user"),
            "PASSWORD": env("POSTGRES_PASSWORD", default="comic_pass"),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default=5432),
        }
    }
```

**說明：**
- 明確覆寫所有安全設定為開發模式
- 不依賴環境變數（開發設定通常是固定的）
- 保持 database 的條件判斷（測試用 SQLite）

### Phase 4：重構 gcr.py（Cloud Run）

```python
# app/src/config/settings/gcr.py
import io
import os
from urllib.parse import urlparse
import environ

from .base import *

# ============================================================
# Cloud Run Production Settings
# ============================================================

# 讀取 Cloud Run 的 APPLICATION_SETTINGS 環境變數
env = environ.Env()
env.read_env(io.StringIO(os.environ.get("APPLICATION_SETTINGS", "")))

# ============================================================
# Security Settings
# ============================================================

# 繼承 base.py 的 Secure by Default 設定
# 如需修改，可透過 APPLICATION_SETTINGS 環境變數覆寫：
# - DEBUG=True (除錯時使用)
# - DJANGO_SECURE_SSL_REDIRECT=False (如需關閉)

# Cloud Run 反向代理設定（必須）
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================================
# Django Core Settings
# ============================================================

# SECRET_KEY - 必須透過環境變數提供
SECRET_KEY = env("SECRET_KEY")

# ============================================================
# CORS & CSRF Settings
# ============================================================

# Cloud Run 使用 Firebase Hosting proxy，屬於同域請求
# 覆寫 base.py 的開發用 CORS 設定

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:9000",
    "https://comicchase.web.app",
]

CORS_EXTRA_ORIGINS_STR = env("CORS_EXTRA_ORIGINS", default="")
if CORS_EXTRA_ORIGINS_STR:
    CORS_ALLOWED_ORIGINS.extend(
        [origin.strip() for origin in CORS_EXTRA_ORIGINS_STR.split(",")]
    )

# CSRF 設定
CLOUDRUN_SERVICE_URLS = env("CLOUDRUN_SERVICE_URLS", default=None)
if CLOUDRUN_SERVICE_URLS:
    CSRF_TRUSTED_ORIGINS = [url.strip() for url in CLOUDRUN_SERVICE_URLS.split(",")]
    ALLOWED_HOSTS = [urlparse(url).netloc for url in CSRF_TRUSTED_ORIGINS]
else:
    ALLOWED_HOSTS = ["*"]
    CSRF_TRUSTED_ORIGINS = ["https://*.run.app", "https://comicchase.web.app"]

# ============================================================
# Database Settings
# ============================================================

# 使用 django-environ 的 env.db() 自動解析 DATABASE_URL
DATABASES = {"default": env.db()}

# Cloud SQL Auth Proxy 設定
if env("USE_CLOUD_SQL_AUTH_PROXY", default=False):
    DATABASES["default"]["HOST"] = "127.0.0.1"
    DATABASES["default"]["PORT"] = 5432

# ============================================================
# Static Files & Storage
# ============================================================

GS_BUCKET_NAME = env("GS_BUCKET_NAME", default="")

if GS_BUCKET_NAME:
    # 使用 Google Cloud Storage
    STATICFILES_DIRS = []
    GS_DEFAULT_ACL = "publicRead"
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        },
        "staticfiles": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        },
    }
else:
    # Fallback: 本地檔案系統 + WhiteNoise
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
```

**重點說明：**
- ✅ 繼承 base.py 的安全設定（Secure by Default）
- ✅ 移除重複的 `DEBUG`、安全設定（由 base.py 統一管理）
- ✅ 只設定 Cloud Run 特有的項目（proxy header, Cloud SQL, GCS）
- ✅ 保留靈活性（可透過環境變數覆寫）

### Phase 5：重構 gce.py（Compute Engine + Firebase Frontend）

```python
# app/src/config/settings/gce.py
from .base import *

# ============================================================
# GCE Production Settings (Firebase Frontend)
# ============================================================

# 繼承 base.py 的所有安全設定（Secure by Default）
# 包括：
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
        "HOST": env("DB_HOST", default="db"),
        "PORT": env("DB_PORT", default=5432),
    }
}

# ============================================================
# Celery Settings
# ============================================================

# 繼承 base.py 的 Celery 設定
# GCE 使用 RabbitMQ（透過環境變數設定）
# CELERY_BROKER_URL = amqp://guest:guest@rabbitmq:5672//
```

**重點說明：**
- ✅ **前後端分離架構**：Frontend 由 Firebase Hosting 提供，Backend 由 GCE 提供
- ✅ 繼承 base.py 的所有安全設定
- ✅ 設定 Firebase Hosting domain 為 ALLOWED_HOSTS
- ✅ 加上 CORS 設定（雖然 Firebase rewrite 是同域，但作為防禦性編程）
- ✅ 保留 Celery 支援（使用 RabbitMQ）

---

## 📋 設定項目總覽

### 各環境設定項目對照表

| 設定項目 | base.py | local.py | gcr.py | gce.py |
|---------|---------|----------|--------|--------|
| **DEBUG** | `False` (預設) | ✅ 覆寫為 `True` | 繼承 | 繼承 |
| **SECRET_KEY** | ✅ 有預設值 | 繼承 | ✅ 必須提供 | ✅ 必須提供 |
| **SECURE_SSL_REDIRECT** | `True` (預設) | ✅ 覆寫為 `False` | 繼承 | 繼承 |
| **CSRF_COOKIE_SECURE** | `True` (預設) | ✅ 覆寫為 `False` | 繼承 | 繼承 |
| **SESSION_COOKIE_SECURE** | `True` (預設) | ✅ 覆寫為 `False` | 繼承 | 繼承 |
| **SECURE_HSTS_SECONDS** | `31536000` (預設) | ✅ 覆寫為 `0` | 繼承 | 繼承 |
| **SECURE_HSTS_INCLUDE_SUBDOMAINS** | `True` (預設) | 繼承 | 繼承 | 繼承 |
| **SECURE_HSTS_PRELOAD** | `True` (預設) | 繼承 | 繼承 | 繼承 |
| **SECURE_PROXY_SSL_HEADER** | ❌ 不設定 | ❌ 不需要 | ✅ 必須設定 | ✅ 必須設定 |
| **CORS_ALLOWED_ORIGINS** | ✅ 開發用 | 繼承 | ✅ 覆寫 | ✅ 設定（Firebase） |
| **CSRF_TRUSTED_ORIGINS** | ✅ 開發用 | 繼承 | ✅ 覆寫 | ✅ 覆寫 |
| **ALLOWED_HOSTS** | `["*"]` | 繼承 | ✅ 動態設定 | ✅ Firebase domains |
| **DATABASES** | ❌ 不設定 | ✅ 設定 | ✅ 設定 | ✅ 設定 |
| **CELERY_*** | ✅ 完整設定 | 繼承 | 繼承（不使用） | 繼承（使用） |

---

## 🔧 環境變數設定指南

### local.py（開發環境）

**不需要設定環境變數**（所有設定都硬編碼在 `local.py`）

可選的 `.env` 檔案（僅用於覆寫資料庫等設定）：
```bash
# app/.env（可選）
POSTGRES_DB=comic_db
POSTGRES_USER=comic_user
POSTGRES_PASSWORD=comic_pass
DB_HOST=localhost
DB_PORT=5432
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
```

### gcr.py（Cloud Run）

**必須設定的環境變數（透過 `APPLICATION_SETTINGS`）：**
```bash
# Cloud Run 環境變數
APPLICATION_SETTINGS='
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgres://user:pass@/dbname?host=/cloudsql/project:region:instance
'

# 可選的環境變數
APPLICATION_SETTINGS='
DEBUG=False
DJANGO_SECURE_SSL_REDIRECT=True
GS_BUCKET_NAME=your-bucket-name
CLOUDRUN_SERVICE_URLS=https://your-service.run.app
CORS_EXTRA_ORIGINS=https://example.com
USE_CLOUD_SQL_AUTH_PROXY=False
'
```

### gce.py（Compute Engine）

**必須設定的環境變數：**
```bash
# .env 或系統環境變數
SECRET_KEY=your-secret-key-here
POSTGRES_DB=comic_db
POSTGRES_USER=comic_user
POSTGRES_PASSWORD=secure-password
DB_HOST=db
DB_PORT=5432
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
```

**可選的環境變數：**
```bash
# 如需暫時開啟 DEBUG（不建議）
DEBUG=True

# 如需調整 HSTS 時間
DJANGO_SECURE_HSTS_SECONDS=3600
```

---

## ✅ 實施步驟

### Step 1: 備份現有設定

```bash
cd /home/atwolin/Documents/Programming/Projects/ComicChase
git checkout -b refactor/django-settings
```

### Step 2: 更新依賴

```bash
# 編輯 app/requirements.txt
# 移除：python-decouple
# 確認有：django-environ>=0.11.2
```

### Step 3: 重構設定檔

按照以下順序修改：

1. ✅ **base.py** - 建立統一的真相來源
2. ✅ **local.py** - 覆寫開發設定
3. ✅ **gcr.py** - 簡化 Cloud Run 設定
4. ✅ **gce.py** - 簡化 GCE 設定

### Step 4: 測試各環境

```bash
# 測試 local.py
DJANGO_SETTINGS_MODULE=config.settings.local python manage.py check

# 測試 gcr.py（需要設定環境變數）
export APPLICATION_SETTINGS='SECRET_KEY=test\nDATABASE_URL=sqlite:///db.sqlite3'
DJANGO_SETTINGS_MODULE=config.settings.gcr python manage.py check

# 測試 gce.py（需要設定環境變數）
export SECRET_KEY=test POSTGRES_DB=test POSTGRES_USER=test POSTGRES_PASSWORD=test
DJANGO_SETTINGS_MODULE=config.settings.gce python manage.py check
```

### Step 5: 提交變更

```bash
git add app/src/config/settings/
git commit -m "refactor: 統一使用 django-environ 並採用 Secure by Default 策略"
```

---

## 📊 Before & After 比較

### DEBUG 設定

**Before（不安全）：**
```python
# base.py - 沒有設定，或被註解
# local.py - DEBUG = True
# gcr.py - DEBUG = env("DEBUG")  # 若未設定會報錯
# gce.py - DEBUG = False
```

**After（Secure by Default）：**
```python
# base.py - DEBUG = env('DEBUG', default=False)  # 安全預設值
# local.py - DEBUG = True  # 明確覆寫
# gcr.py - 繼承 base.py（可透過環境變數覆寫）
# gce.py - 繼承 base.py（可透過環境變數覆寫）
```

### SECRET_KEY 設定

**Before（重複）：**
```python
# base.py - SECRET_KEY = config("SECRET_KEY", default="...")
# gcr.py - SECRET_KEY = env("SECRET_KEY")  # 重複
# gce.py - SECRET_KEY = config("SECRET_KEY")  # 重複
```

**After（DRY）：**
```python
# base.py - SECRET_KEY = env("SECRET_KEY", default="...")
# gcr.py - SECRET_KEY = env("SECRET_KEY")  # 必須覆寫（production 要求）
# gce.py - SECRET_KEY = env("SECRET_KEY")  # 必須覆寫（production 要求）
```

### 安全設定

**Before（gcr.py 缺少）：**
```python
# gcr.py - 沒有任何 HTTPS/SSL 安全設定
```

**After（完整）：**
```python
# base.py - 完整的安全設定（預設啟用）
# gcr.py - 繼承所有安全設定 + SECURE_PROXY_SSL_HEADER
```

---

## 🎯 預期效果

### 1. **安全性提升**
- ✅ 預設使用最安全的設定
- ✅ 環境變數載入失敗時使用安全預設值
- ✅ gcr.py 新增完整的 HTTPS/SSL 安全設定

### 2. **程式碼簡化**
- ✅ gcr.py 減少 ~10 行重複設定
- ✅ gce.py 減少 ~5 行重複設定
- ✅ 統一使用 django-environ，移除 python-decouple

### 3. **維護性提升**
- ✅ 單一真相來源（base.py）
- ✅ 各環境檔案更簡潔
- ✅ 新增環境時不需要重複設定安全項目

### 4. **靈活性保持**
- ✅ 所有設定都可透過環境變數覆寫
- ✅ 開發環境明確覆寫（不依賴環境變數）
- ✅ 生產環境繼承安全預設值

---

## 📚 參考資料

1. **Django for Professionals** by William S. Vincent - Secure by Default 原則
2. **Two Scoops of Django** - Django settings 最佳實踐
3. **12-Factor App** - [https://12factor.net/config](https://12factor.net/config)
4. **django-environ 文件** - [https://django-environ.readthedocs.io/](https://django-environ.readthedocs.io/)
5. **Django Security Settings** - [https://docs.djangoproject.com/en/stable/topics/security/](https://docs.djangoproject.com/en/stable/topics/security/)

---

## 💡 未來改進建議

### 1. 建立 staging 環境

```python
# staging.py（未來可新增）
from .base import *

# 繼承所有安全設定，只需設定 staging 特有的項目
ALLOWED_HOSTS = ["staging.comicchase.com.tw"]
```

### 2. 使用 Secret Manager

對於敏感資訊（如 SECRET_KEY），考慮使用：
- Google Cloud Secret Manager
- AWS Secrets Manager
- HashiCorp Vault

### 3. 環境變數驗證

在 `base.py` 加入驗證：

```python
# 確保 production 環境必須設定 SECRET_KEY
if not DEBUG and SECRET_KEY == 'django-insecure-test-key-for-development-only':
    raise ImproperlyConfigured("SECRET_KEY must be set in production")
```

---

**文件版本：** 1.0
**最後更新：** 2026-01-06
**作者：** ComicChase Development Team

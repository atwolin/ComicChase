# 快速開始指南

本指南將帶領你在本地環境啟動 ComicChase 開發環境。

## 前置條件檢查

確保你已安裝以下軟體：

```bash
docker --version      # 需要 >= 28.5.2
docker compose version # 需要 >= v2.39.2
git --version         # 需要 >= 2.30
```

> 如果尚未安裝，請參考 [requirements.md](./requirements.md#必要軟體)

## 快速啟動

### 1️⃣ Clone 專案

```bash
git clone https://github.com/atwolin/ComicChase.git
cd ComicChase
```

### 2️⃣ 設定環境變數

```bash
# 複製範例檔案
cp .env.example .env

# 快速設定（使用預設值）
cat > .env << 'EOF'
GID=1000
UID=1000

# Django settings
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_SETTINGS_MODULE=config.settings.local
SECRET_KEY=dev-secret-key-change-in-production

# Database settings
DB_HOST=db
DB_PORT=5432
POSTGRES_DB=comicchase_dev
POSTGRES_PASSWORD=comicchase123
POSTGRES_USER=comicchase

# Email settings
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_DEFAULT_REGION=your-default-region
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_SES_REGION=your-ses-region
AWS_SES_REGION_ENDPOINT=your-ses-region-endpoint
DEFAULT_FROM_EMAIL=your-email@your-domain.com
EMAIL_BACKEND=django_ses.SESBackend

# Celery settings
CELERY_BROKER_URL=amqp://admin:admin@rabbitmq:5672/staging_vhost

# RabbitMQ settings
RABBITMQ_DEFAULT_PASS=admin
RABBITMQ_DEFAULT_USER=admin
RABBITMQ_DEFAULT_VHOST=staging_vhost
EOF
```

> ⚠️ **生產環境請務必修改密碼與 SECRET_KEY**

### 3️⃣ 啟動所有服務

```bash
# 建置並啟動所有 Docker 容器
make rebuild

# 等待所有服務啟動完成
# 你可以用以下指令查看狀態
docker compose ps
```

### 4️⃣ 初始化資料庫

```bash
# 進入 backend 容器
make shell

# 執行資料庫遷移
python manage.py migrate

# 建立管理員帳號（username: admin, password: 自訂）
python manage.py createsuperuser

# 離開容器
exit
```

### 5️⃣ 驗證服務

開啟瀏覽器，存取以下網址：

| 服務 | URL | 說明 |
|------|-----|------|
| 🎨 **前端** | <http://localhost:3000> | React 應用程式 |
| 🔧 **Django Admin** | <http://localhost:8000/admin> | 後台管理 (使用你剛建立的帳號登入) |
| 📖 **API 文件** | <http://localhost:8000/api/schema/swagger-ui/> | Swagger UI |
| 🌼 **Flower** | <http://localhost:5555> | Celery 任務監控 |
| 🐰 **RabbitMQ** | <http://localhost:15672> | 訊息佇列管理介面 (帳密: admin/admin) |
| 🌐 **Selenium Grid** | <http://localhost:4444> | 瀏覽器自動化網格 |

---

## 常用開發指令

```bash
# 查看服務狀態
docker compose ps

# 查看日誌（即時追蹤）
make logs SERV=backend        # Django 後端
make logs SERV=celery-crawler # 爬蟲 worker
make logs SERV=ui             # React 前端

# 重啟特定服務
docker compose restart backend
docker compose restart celery-crawler

# 停止所有服務
make down

# 重新啟動（不重新建置）
make up

# 完全清理（包含 volumes）
make clean

# 更新前端 API
cd ui
npm run generate:api
```

---

## 安裝 Pre-commit Hooks

Pre-commit hooks 會在 commit 前自動檢查程式碼品質。

```bash
# 安裝 pre-commit
pip install pre-commit

# 安裝 git hooks
pre-commit install

# 測試執行（對所有檔案）
pre-commit run --all-files
```

**前端 hooks 需要 Node.js 依賴:**
```bash
cd ui
npm install
```

---

## 參考資源

- **詳細環境需求**: [requirements.md](./requirements.md)
- **API 文件**: <http://localhost:8000/api/schema/swagger-ui/> (啟動服務後)
- **系統架構圖**: [README.md](../../README.md#系統架構)
- **部署指南**: [docs/2-Deployment/](../2-Deployment/)

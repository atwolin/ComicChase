# 郵件通知定期任務設置完成總結

## ✅ 已創建的文件

### **1. 核心功能文件**

#### **Management Command**
- **位置**: `app/src/subscriptions/management/commands/run_scheduled_email.py`
- **用途**: Django management command，支持 Cloud Run Jobs 的同步執行
- **使用方式**:
  ```bash
  python manage.py run_scheduled_email --task weekly_digest
  ```

#### **Shell 腳本**
- **位置**: `app/src/run_email.sh`
- **用途**: 在 Cloud Run Jobs 中執行郵件任務的入口腳本
- **使用方式**:
  ```bash
  EMAIL_TASK=weekly_digest bash run_email.sh
  ```
- **權限**: 已設置為可執行 (chmod +x)

---

### **2. 已更新的文件**

#### **Tasks 文件**
- **位置**: `app/src/subscriptions/tasks.py`
- **修改內容**:
  - 修復 `run_weekly_notification_flow` 的 `task_id` 取得邏輯
  - 確保 `sync` 參數正確傳遞
  - 支持同步執行（Cloud Run Jobs）和異步執行（Celery）

---

### **3. 文檔文件**

#### **詳細部署指南**
- **位置**: `docs/2-Deployment/email-notification-scheduler.md`
- **內容**:
  - 任務概覽
  - 本機測試方法
  - Cloud Run Jobs 完整部署步驟
  - Cloud Scheduler 設置
  - 監控與維護指南
  - 成本估算
  - 故障排除

#### **本機測試指南**
- **位置**: `docs/2-Deployment/email-notification-local-testing-guide.md`
- **內容**:
  - 測試前準備
  - 5 種詳細測試方法
  - 測試檢查清單
  - 常見問題排除
  - 測試通過標準

#### **快速參考**
- **位置**: `docs/2-Deployment/email-notification-quickref.md`
- **內容**:
  - 常用指令快速參考
  - 部署指令
  - 監控指令
  - 管理指令
  - 故障排除快速指南

---

## 🎯 架構設計

### **參考 comic_scrapers 的架構**

郵件通知任務完全參考 `comic_scrapers` 的定期任務架構：

1. **同步/異步雙模式執行**
   - `sync=True`: 用於 Cloud Run Jobs（同步執行）
   - `sync=False`: 用於 Celery Worker（異步執行）

2. **Django Management Command**
   - 提供統一的任務執行入口
   - 支持 `--task` 參數指定不同任務

3. **Shell 腳本包裝器**
   - 通過環境變數 `EMAIL_TASK` 指定任務
   - 在 Cloud Run Jobs 中作為 entrypoint

4. **完整的錯誤處理和日誌記錄**
   - 詳細的執行過程日誌
   - 錯誤時返回正確的 exit code

---

## 📋 可用的郵件任務

| 任務名稱 | 環境變數值 | 說明 | 建議頻率 |
|---------|-----------|------|---------|
| **每週摘要** | `weekly_digest` | 發送每週新出版漫畫清單 | 每週一次 |

---

## 🚀 快速開始

### **本機測試（推薦先執行）**

```bash
# 在 WSL 終端機
cd /mnt/c/Users/ameli/ComicChase

# 方法 1: 使用 Management Command
python app/src/manage.py run_scheduled_email --task weekly_digest

# 方法 2: 使用 Shell 腳本
EMAIL_TASK=weekly_digest bash app/src/run_email.sh
```

---

### **Cloud Run 部署**

```bash
# 1. 設定環境變數
PROJECT_ID=$(gcloud config get-value core/project)
REGION=us-central1
SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter cloudrun-serviceaccount --format "value(email)")
IMAGE=${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service
INSTANCE_NAME=comic-instance

# 2. 創建 Cloud Run Job
gcloud run jobs create email-weekly-digest-job \
  --image ${IMAGE} \
  --region ${REGION} \
  --service-account ${SERVICE_ACCOUNT} \
  --set-env-vars EMAIL_TASK=weekly_digest \
  --set-cloudsql-instances ${PROJECT_ID}:${REGION}:${INSTANCE_NAME} \
  --set-secrets application_settings=application_settings:latest \
  --memory 512Mi \
  --cpu 1 \
  --max-retries 2 \
  --task-timeout 30m \
  --command bash \
  --args /code/app/src/run_email.sh

# 3. 手動測試
gcloud run jobs execute email-weekly-digest-job --region ${REGION}

# 4. 創建定期排程（每週一早上 9:00）
gcloud scheduler jobs create http email-weekly-digest-schedule \
  --location ${REGION} \
  --schedule "0 9 * * 1" \
  --time-zone "Asia/Taipei" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/email-weekly-digest-job:run" \
  --http-method POST \
  --oauth-service-account-email ${SERVICE_ACCOUNT}
```

---

## 📊 與 comic_scrapers 架構對比

### **相同點**

| 功能 | comic_scrapers | email_notification |
|------|---------------|-------------------|
| **同步執行支持** | ✅ | ✅ |
| **異步執行支持** | ✅ | ✅ |
| **Management Command** | ✅ | ✅ |
| **Shell 腳本** | ✅ | ✅ |
| **Cloud Run Jobs** | ✅ | ✅ |
| **Cloud Scheduler** | ✅ | ✅ |
| **錯誤處理** | ✅ | ✅ |
| **詳細日誌** | ✅ | ✅ |

### **差異點**

| 項目 | comic_scrapers | email_notification |
|------|---------------|-------------------|
| **任務數量** | 4 個 (bookstw_new, eslite_all_series, booksjp_all_series, eslite_orphan_volumes) | 1 個 (weekly_digest) |
| **執行時長** | 各不相同（15分鐘 - 2小時） | ~5 分鐘 |
| **資源需求** | CPU: 1-2, Memory: 2-4Gi | CPU: 1, Memory: 512Mi |
| **外部服務** | 無 | AWS SES |
| **環境變數名稱** | `CRAWLER_TASK` | `EMAIL_TASK` |

---

## 💡 使用建議

### **開發階段**

1. **先在本機測試**
   - 使用 `python manage.py run_scheduled_email --task weekly_digest`
   - 確認郵件發送成功
   - 檢查郵件內容和格式

2. **確認 AWS SES 設置**
   - 驗證發件人郵箱
   - 如果在沙盒模式，驗證收件人郵箱
   - 申請移出沙盒模式（生產環境）

3. **測試數據準備**
   - 確保資料庫有近期新書資料
   - 創建測試用戶

---

### **部署階段**

1. **先手動執行 Cloud Run Job**
   - 測試 Job 是否正常執行
   - 查看日誌確認無錯誤
   - 確認郵件發送成功

2. **再設置 Cloud Scheduler**
   - 手動觸發測試排程
   - 確認排程能正確觸發 Job

3. **設置監控和告警**
   - 使用 Cloud Monitoring 監控執行狀態
   - 設置失敗告警

---

### **維護階段**

1. **定期檢查**
   - 每週檢查執行狀態
   - 每月檢查成本使用
   - 定期更新 Docker Image

2. **日誌監控**
   - 使用 Cloud Logging 查看執行日誌
   - 監控錯誤和異常

---

## 🔗 相關資源

### **項目文檔**

- [email-notification-scheduler.md](./email-notification-scheduler.md) - 詳細部署指南
- [email-notification-local-testing-guide.md](./email-notification-local-testing-guide.md) - 本機測試指南
- [email-notification-quickref.md](./email-notification-quickref.md) - 快速參考

### **參考文檔**

- [cloud-backend-crawler-run-jobs-scheduler.md](./cloud-backend-crawler-run-jobs-scheduler.md) - 爬蟲任務參考
- [crawler-run-jobs-local-testing-guide.md](./crawler-run-jobs-local-testing-guide.md) - 爬蟲測試參考

### **外部資源**

- [Cloud Run Jobs 官方文件](https://cloud.google.com/run/docs/create-jobs)
- [Cloud Scheduler 官方文件](https://cloud.google.com/scheduler/docs)
- [AWS SES 官方文件](https://docs.aws.amazon.com/ses/)
- [Cron 格式參考](https://crontab.guru/)

---

## 📝 下一步

### **立即可做**

1. **本機測試郵件任務**
   ```bash
   python app/src/manage.py run_scheduled_email --task weekly_digest
   ```

2. **檢查郵件模板**
   - 查看 `app/src/templates/emails/weekly_digest.html`
   - 測試不同數據情況的渲染效果

3. **確認 AWS SES 設置**
   ```bash
   aws ses list-verified-email-addresses --region us-east-1
   ```

---

### **部署前準備**

1. **建置 Docker Image**
   ```bash
   docker build -f app/Dockerfile \
     -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service .
   ```

2. **推送到 Artifact Registry**
   ```bash
   docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service
   ```

3. **部署到 Cloud Run Jobs**
   - 參考 `email-notification-scheduler.md`

---

## ✅ 完成狀態

- [x] 創建 Django Management Command
- [x] 創建 Shell 腳本
- [x] 更新 tasks.py 支持同步執行
- [x] 創建詳細部署文檔
- [x] 創建本機測試文檔
- [x] 創建快速參考文檔
- [x] 設置正確的文件權限
- [ ] 本機測試郵件發送（等待執行）
- [ ] 部署到 Cloud Run Jobs（等待執行）
- [ ] 設置 Cloud Scheduler（等待執行）

---

**文件版本：** 1.0  
**創建日期：** 2026-01-13  
**作者：** AI Assistant

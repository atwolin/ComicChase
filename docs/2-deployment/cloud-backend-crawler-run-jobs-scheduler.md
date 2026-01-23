# Cloud Run Jobs + Cloud Scheduler 定期爬蟲設定指南

## 📋 文件目的

本文件說明如何在 Google Cloud Run (GCR) 環境下，使用 **Cloud Scheduler** + **Cloud Run Jobs** 來執行定期爬蟲任務，完全無需 Celery Worker 或 RabbitMQ。

**最後更新：** 2026-01-06
**文件版本：** 2.0

---

## 🏗️ 架構概覽

### **架構圖**

```bash
┌─────────────────────────────────────────────────────────┐
│                   Google Cloud Project                  │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │  Cloud Run Service (Web API)                   │     │
│  │  - 使用者訪問時才啟動                             │     │
│  │  - 沒流量時 scale to zero                       │     │
│  │  - 不負責執行爬蟲                                │     │
│  └────────────────────────────────────────────────┘     │
│                                                         │
│  ┌────────────────────────────────────────────────┐     │
│  │  Cloud Scheduler (定時觸發器)                   │     │
│  │  ✅ bookstw-new-release-schedule (每天 02:00)  │     │
│  │  ✅ eslite-title-schedule (每週日 03:00)        │     │
│  │  ✅ booksjp-title-schedule (每週六 03:00)       │     │
│  │  ✅ eslite-orphan-schedule (每月 1 號 04:00)    │     │
│  └──────────────┬─────────────────────────────────┘     │
│                 │ (HTTP POST 觸發)                      │
│                 ↓                                       │
│  ┌────────────────────────────────────────────────┐     │
│  │  Cloud Run Jobs (爬蟲任務，獨立運行)              │     │
│  │                                                │     │
│  │  ✅ bookstw-daily-crawler                      │     │
│  │  ✅ eslite-title-crawler                       │     │
│  │  ✅ booksjp-title-crawler                      │     │
│  │  ✅ eslite-orphan-crawler                      │     │
│  │                                                │     │
│  │  執行流程：                                     │      │
│  │  1. 收到 Scheduler 觸發                         │     │
│  │  2. 啟動 Container                             │      │
│  │  3. 執行 run_crawler.sh                        │      │
│  │  4. 呼叫 tasks.py 中的批次任務                   │      │
│  │  5. 查詢資料庫 → 同步執行爬蟲                     │      │
│  │  6. 完成後自動關閉                               │     │
│  └──────────────┬─────────────────────────────────┘     │
│                 │                                       │
│                 ↓ (寫入爬蟲資料)                          │
│  ┌────────────────────────────────────────────────┐     │
│  │  Cloud SQL (PostgreSQL)                        │     │
│  │  - Series, Volume 資料                          │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### **執行流程詳解**

```bash
Cloud Scheduler (定時觸發)
    ↓ HTTP POST
Cloud Run Job (啟動全新 Container)
    ↓ 執行命令
/bin/bash /code/app/run_crawler.sh
    ↓ 根據環境變數決定任務
python manage.py run_scheduled_crawler --task ${CRAWLER_TASK}
    ↓ 直接呼叫 Celery Task Function（同步執行）
tasks.crawl_all_series_eslite()
    ↓ 查詢資料庫
Series.objects.filter(title_tw__isnull=False)
    ↓ 批次執行（同步，逐一爬取）
for title, last_date in series_list:
    call_command('eslite_title_search', title=title, last_release_date=last_date)
    ↓
執行 Scrapy Spider → 爬取資料 → Pipeline 寫入 Cloud SQL
```

---

## ✅ 優點分析

相較於 Celery + RabbitMQ (GCE 方案)：

| 項目 | Celery + RabbitMQ | Cloud Run Jobs |
| ------ | ------------------ | ---------------- |
| **基礎設施** | ⚠️ 需要 RabbitMQ VM | ✅ Serverless（無需管理） |
| **成本** | ⚠️ VM 持續運行（~$30-50/月） | ✅ 按執行時間計費（~$0.5-2/月） |
| **擴展性** | ⚠️ 受限於 VM 資源 | ✅ 自動擴展 |
| **維護** | ⚠️ 需維護 RabbitMQ、Celery Worker | ✅ 完全託管 |
| **可靠性** | ⚠️ Worker 可能當機 | ✅ Google 管理，自動重試 |
| **監控** | ⚠️ 需自行設定 | ✅ Cloud Logging 整合 |
| **適合場景** | 頻繁、即時任務 | ✅ **定期、批次任務（我們的需求）** |

---

## 🔧 實作步驟

### **前置需求**

- ✅ 已部署 Cloud Run Service（Web API）
- ✅ 已設定 Cloud SQL 資料庫
- ✅ 已建置 Docker Image（`${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service`）
- ✅ 已設定 Service Account 並授予權限（`cloudrun-serviceaccount`）

---

### **Step 1: 修改 `tasks.py` 支援同步執行**

**檔案位置：** `app/src/comic_scrapers/tasks.py`

在每個批次任務中增加 `sync` 參數，允許同步執行（不透過 Celery Worker）：

**修改的任務：**

- `crawl_all_series_eslite`
- `crawl_all_series_booksjp(sync=False)`
- `crawl_orphan_volumes_eslite(sync=False)`
- `crawl_new_volumes_bookstw(sync=False)` (此任務已經不需要分批，保持 sync 參數即可)

---

### **Step 2: 建立 Management Command**

**檔案位置：** `app/src/comic_scrapers/management/commands/run_scheduled_crawler.py`

---

### **Step 3: 建立 Shell 執行腳本**

**檔案位置：** `app/src/run_crawler.sh`

---

### **Step 4: 更新 Dockerfile.gcr**

**檔案位置：** `app/Dockerfile.gcr`

確保 `run_crawler.sh` 有執行權限：

```dockerfile
# ... 其他設定 ...

COPY ./app/src ./

# 賦予腳本執行權限
RUN chmod +x entrypoint.gcr.sh wait-for-it.sh run_crawler.sh

# ... 其他設定 ...
```

---

### **Step 5: 建置並推送 Docker Image**

```bash
# 在專案根目錄
cd /path/to/ComicChase

# 設定環境變數（替換為您的專案）
PROJECT_ID=$(gcloud config get-value core/project)
REGION="us-central1"

# 建置 image
docker build -f app/Dockerfile.gcr -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service .

# 推送到 Artifact Registry
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service
```

---

### **Step 6: 建立 Cloud Run Jobs**

#### **設定環境變數（簡化後續指令）**

```bash
export PROJECT_ID=$(gcloud config get-value core/project)
export REGION="us-central1"
export INSTANCE_NAME="comic-instance"
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service"
export SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
    --filter cloudrun-serviceaccount --format "value(email)")
export CLOUDSQL_INSTANCE="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"
```

---

#### **Job 1: 每日新書爬蟲（books.com.tw）**

```bash
gcloud run jobs create bookstw-daily-crawler \
  --image ${IMAGE} \
  --region ${REGION} \
  --set-env-vars "CRAWLER_TASK=bookstw_new" \
  --set-env-vars "DJANGO_SETTINGS_MODULE=config.settings.gcr" \
  --set-secrets "APPLICATION_SETTINGS=application_settings:latest" \
  --set-cloudsql-instances ${CLOUDSQL_INSTANCE} \
  --service-account ${SERVICE_ACCOUNT} \
  --task-timeout 60m \
  --max-retries 2 \
  --memory 2Gi \
  --cpu 1 \
  --command "/bin/bash" \
  --args "/code/app/run_crawler.sh"
```

**說明：**

- `--task-timeout 60m`: 爬蟲最多執行 60 分鐘
- `--max-retries 2`: 失敗時最多重試 2 次
- `--memory 2Gi`: 分配 2GB 記憶體（Selenium 需要較多記憶體）
- `--cpu 1`: 使用 1 個 vCPU

---

#### **Job 2: 每週更新所有系列（誠品）**

```bash
gcloud run jobs create eslite-title-crawler \
  --image ${IMAGE} \
  --region ${REGION} \
  --set-env-vars "CRAWLER_TASK=eslite_all_series" \
  --set-env-vars "DJANGO_SETTINGS_MODULE=config.settings.gcr" \
  --set-secrets "APPLICATION_SETTINGS=application_settings:latest" \
  --set-cloudsql-instances ${CLOUDSQL_INSTANCE} \
  --service-account ${SERVICE_ACCOUNT} \
  --task-timeout 2h \
  --max-retries 1 \
  --memory 2Gi \
  --cpu 2 \
  --command "/bin/bash" \
  --args "/code/app/run_crawler.sh"
```

**說明：**

- `--task-timeout 2h`: 爬取所有系列可能需要較長時間
- `--cpu 2`: 使用 2 個 vCPU 加速處理

---

#### **Job 3: 每週更新所有系列（Books.jp）**

```bash
gcloud run jobs create booksjp-title-crawler \
  --image ${IMAGE} \
  --region ${REGION} \
  --set-env-vars "CRAWLER_TASK=booksjp_all_series" \
  --set-env-vars "DJANGO_SETTINGS_MODULE=config.settings.gcr" \
  --set-secrets "APPLICATION_SETTINGS=application_settings:latest" \
  --set-cloudsql-instances ${CLOUDSQL_INSTANCE} \
  --service-account ${SERVICE_ACCOUNT} \
  --task-timeout 2h \
  --max-retries 1 \
  --memory 2Gi \
  --cpu 2 \
  --command "/bin/bash" \
  --args "/code/app/run_crawler.sh"
```

---

#### **Job 4: 每月 Orphan Volumes 清理（誠品）**

```bash
gcloud run jobs create eslite-orphan-crawler \
  --image ${IMAGE} \
  --region ${REGION} \
  --set-env-vars "CRAWLER_TASK=eslite_orphan_volumes" \
  --set-env-vars "DJANGO_SETTINGS_MODULE=config.settings.gcr" \
  --set-secrets "APPLICATION_SETTINGS=application_settings:latest" \
  --set-cloudsql-instances ${CLOUDSQL_INSTANCE} \
  --service-account ${SERVICE_ACCOUNT} \
  --task-timeout 1h \
  --max-retries 2 \
  --memory 2Gi \
  --cpu 1 \
  --command "/bin/bash" \
  --args "/code/app/run_crawler.sh"
```

---

### **Step 7: 設定 Cloud Scheduler 定期觸發**

#### **排程 1: 每天凌晨 2 點爬新書（books.tw）**

```bash
gcloud scheduler jobs create http bookstw-new-release-schedule \
  --location ${REGION} \
  --schedule "0 2 * * *" \
  --time-zone "Asia/Taipei" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/bookstw-daily-crawler:run" \
  --http-method POST \
  --oauth-service-account-email ${SERVICE_ACCOUNT}
```

**Cron 格式說明：**

- `0 2 * * *` = 每天凌晨 2:00（台北時間）

---

#### **排程 2: 每週日凌晨 3 點更新所有系列（誠品）**

```bash
gcloud scheduler jobs create http eslite-title-schedule \
  --location ${REGION} \
  --schedule "0 3 * * 0" \
  --time-zone "Asia/Taipei" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/eslite-title-crawler:run" \
  --http-method POST \
  --oauth-service-account-email ${SERVICE_ACCOUNT}
```

**Cron 格式：**

- `0 3 * * 0` = 每週日凌晨 3:00

---

#### **排程 3: 每週六凌晨 3 點更新所有系列（Books.jp）**

```bash
gcloud scheduler jobs create http booksjp-title-schedule \
  --location ${REGION} \
  --schedule "0 3 * * 6" \
  --time-zone "Asia/Taipei" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/booksjp-title-crawler:run" \
  --http-method POST \
  --oauth-service-account-email ${SERVICE_ACCOUNT}
```

**Cron 格式：**

- `0 3 * * 6` = 每週六凌晨 3:00

---

#### **排程 4: 每月 1 日清理 Orphan Volumes（誠品）**

```bash
gcloud scheduler jobs create http eslite-orphan-schedule \
  --location ${REGION} \
  --schedule "0 4 1 * *" \
  --time-zone "Asia/Taipei" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/eslite-orphan-crawler:run" \
  --http-method POST \
  --oauth-service-account-email ${SERVICE_ACCOUNT}
```

**Cron 格式：**

- `0 4 1 * *` = 每月 1 日凌晨 4:00

### **Step 8: 更新**

```bash
gcloud run jobs update bookstw-daily-crawler --image ${IMAGE} --region ${REGION}
gcloud run jobs update eslite-orphan-crawler --image ${IMAGE} --region ${REGION}
gcloud run jobs update eslite-title-crawler --image ${IMAGE} --region ${REGION}
gcloud run jobs update booksjp-title-crawler --image ${IMAGE} --region ${REGION}
```

---

## 🧪 測試與驗證

### **1. 手動觸發 Cloud Run Job（測試）**

在部署完成後，先手動執行一次驗證功能：

```bash
# 手動執行 books.tw 每日爬蟲
gcloud run jobs execute bookstw-daily-crawler --region ${REGION}

# 查看執行狀態
gcloud run jobs executions list --job bookstw-daily-crawler --region ${REGION}
```

**預期輸出：**

```bash
EXECUTION                                      STATUS     STARTED              COMPLETED            DURATION
bookstw-daily-crawler-xn4k2                   Succeeded  2026-01-06 15:00:00  2026-01-06 15:15:00  15m
```

---

### **2. 查看執行日誌**

```bash
# 查看特定 Job 的所有日誌
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=bookstw-daily-crawler" \
  --limit 50 \
  --format json

# 或使用更簡潔的格式
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=bookstw-daily-crawler" \
  --limit 20 \
  --format "table(timestamp, textPayload)"
```

**預期看到的日誌：**

```bash
=========================================
Cloud Run Crawler Job
=========================================
Task: bookstw_new
Started: 2026-01-06 15:00:00 UTC
=========================================
📚 Running books.com.tw new releases crawler...
=== Starting scheduled task: bookstw_new ===
...
✅ Crawler Job Completed
Finished: 2026-01-06 15:15:00 UTC
=========================================
```

---

### **3. 手動觸發 Cloud Scheduler（測試排程）**

```bash
# 手動觸發排程（不等到排定時間）
gcloud scheduler jobs run bookstw-new-release-schedule --location ${REGION}

# 查看排程狀態
gcloud scheduler jobs describe bookstw-new-release-schedule --location ${REGION}
```

---

### **4. 驗證資料庫資料**

執行完爬蟲後，檢查 Cloud SQL 是否有新增資料：

```bash
# 連線到 Cloud SQL (使用預設的資料庫實例名稱)
gcloud sql connect ${INSTANCE_NAME} --user=postgres

# 查詢最近新增的 Volume
SELECT id, title_tw, release_date_tw, created_at
FROM comic_volume
ORDER BY created_at DESC
LIMIT 10;
```

---

## 📊 監控與維護

### **查看所有 Cloud Run Jobs**

```bash
# 列出所有 Jobs
gcloud run jobs list --region ${REGION}

# 查看特定 Job 的詳細資訊
gcloud run jobs describe bookstw-daily-crawler --region ${REGION}
```

---

### **查看所有 Cloud Scheduler**

```bash
# 列出所有排程
gcloud scheduler jobs list --location ${REGION}

# 查看特定排程的詳細資訊
gcloud scheduler jobs describe bookstw-new-release-schedule --location ${REGION}
```

---

### **設定失敗通知（選用）**

使用 Cloud Monitoring 設定 Alert Policy：

1. 前往 **Cloud Console** → **Monitoring** → **Alerting**
2. 點擊 **Create Policy**
3. 設定條件：
   - **Resource Type**: Cloud Run Job
   - **Metric**: Execution Status
   - **Filter**: `status = "Failed"`
4. 設定通知渠道（Email, Slack 等）

---

## 💰 成本估算

### **Cloud Run Jobs 計費**

按**實際執行時間**計費：

- **CPU**: $0.000018 / vCPU-second
- **記憶體**: $0.000002 / GiB-second

### **範例計算（每月）**

假設每天執行 1 次 `bookstw-daily-crawler`：

- 每次執行 15 分鐘 = 900 秒
- 使用 1 vCPU + 2 GiB 記憶體
- 每月執行 30 次

**成本：**

- CPU: 30 × 900 × 1 × $0.000018 = **$0.65**
- 記憶體: 30 × 900 × 2 × $0.000002 = **$0.14**
- **總計: ~$0.79 / 月**

**所有爬蟲任務（4 個 Jobs）預估總成本：** ~$1.50 - $3.00 / 月

### **Cloud Scheduler 計費**

- **免費額度**: 每月 3 個 jobs 免費
- **超額費用**: $0.10 / job / 月

我們有 4 個 schedulers → 3 個免費 + 1 個付費 = **$0.10 / 月**

### **總計**

**預估每月成本: $1.60 - $3.10 USD**（遠低於 GCE + RabbitMQ 的 $30-50/月）

---

## 🔧 故障排除

### **問題 1: Job 執行失敗（Exit Code 1）**

**可能原因：**

- 環境變數 `CRAWLER_TASK` 未正確設定
- Cloud SQL 連線失敗
- Scrapy spider 錯誤

**解決方法：**

```bash
# 查看詳細錯誤日誌
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=bookstw-daily-crawler AND severity>=ERROR" \
  --limit 20
```

---

### **問題 2: Scheduler 未觸發 Job**

**檢查步驟：**

```bash
# 1. 確認 Scheduler 是否啟用
gcloud scheduler jobs describe bookstw-new-release-schedule --location ${REGION}

# 2. 查看 Scheduler 執行歷史
gcloud logging read \
  "resource.type=cloud_scheduler_job AND resource.labels.job_name=bookstw-new-release-schedule" \
  --limit 10
```

---

### **問題 3: 記憶體不足（OOM Killed）**

**症狀：** Job 在執行中途突然停止，Exit Code 137

**解決方法：** 增加記憶體配置

```bash
# 更新 Job 記憶體從 2Gi 提升到 4Gi
gcloud run jobs update bookstw-daily-crawler \
  --region ${REGION} \
  --memory 4Gi
```

---

## 📝 定期維護檢查清單

### **每週檢查**

- [ ] 查看 Cloud Run Jobs 執行狀態
- [ ] 檢查是否有失敗的執行
- [ ] 驗證資料庫有新增資料

### **每月檢查**

- [ ] 檢閱 Cloud Logging 錯誤日誌
- [ ] 監控成本使用情況
- [ ] 更新 Docker Image（如有程式碼修改）

### **更新 Docker Image 流程**

```bash
# 1. 建置新 Image
docker build -f app/Dockerfile.gcr -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service .

# 2. 推送到 Artifact Registry
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service

# 3. 更新所有 Cloud Run Jobs（使用新 Image）
gcloud run jobs update bookstw-daily-crawler --image ${IMAGE} --region ${REGION}
gcloud run jobs update eslite-title-crawler --image ${IMAGE} --region ${REGION}
gcloud run jobs update booksjp-title-crawler --image ${IMAGE} --region ${REGION}
gcloud run jobs update eslite-orphan-crawler --image ${IMAGE} --region ${REGION}

# 4. 手動測試執行
gcloud run jobs execute bookstw-daily-crawler --region ${REGION}
```

---

## 📚 參考資料

- [Cloud Run Jobs 官方文件](https://cloud.google.com/run/docs/create-jobs)
- [Cloud Scheduler 官方文件](https://cloud.google.com/scheduler/docs)
- [Cron 格式參考](https://crontab.guru/)

---

## 🎯 總結

### **架構優勢**

✅ **完全獨立運行**

- Cloud Run Jobs 與 Cloud Run Service 完全分離
- 即使 Web Service scale to zero，爬蟲仍準時執行

✅ **成本極低**

- 按實際執行時間計費
- 預估每月 $1.60 - $3.10 USD

✅ **零維護**

- 無需管理 RabbitMQ、Celery Worker
- Google Cloud 負責基礎設施管理

✅ **高可靠性**

- 自動重試機制
- Cloud Logging 完整記錄

✅ **易於擴展**

- 需要新增爬蟲任務？只需建立新 Job 和 Scheduler

### **定時排程總覽**

| 爬蟲任務 | 頻率 | Cron | 執行時間（台北） | 預估執行時長 |
| --------- | ------ | ------ | ----------------- | ------------- |
| **books.tw 新書** | 每天 | `0 2 * * *` | 每天 02:00 | ~15 分鐘 |
| **Eslite 所有系列** | 每週 | `0 3 * * 0` | 週日 03:00 | ~1-2 小時 |
| **Books.jp 所有系列** | 每週 | `0 3 * * 6` | 週六 03:00 | ~1-2 小時 |
| **Eslite Orphan Volumes** | 每月 | `0 4 1 * *` | 每月 1 號 04:00 | ~30 分鐘 |

---

**文件版本：** 2.0
**最後更新：** 2026-01-06
**作者：** ComicChase Development Team

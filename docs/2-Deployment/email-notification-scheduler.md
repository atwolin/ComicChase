# 郵件通知定期任務設置指南

本文檔說明如何在本機和 Cloud Run 上配置 ComicChase 的郵件通知定期任務。

---

## 📋 目錄

1. [任務概覽](#任務概覽)
2. [本機測試](#本機測試)
3. [Cloud Run Jobs 部署](#cloud-run-jobs-部署)
4. [Cloud Scheduler 設置](#cloud-scheduler-設置)
5. [監控與維護](#監控與維護)
6. [故障排除](#故障排除)

---

## 📧 任務概覽

### **可用的郵件任務**

| 任務名稱 | 說明 | 建議頻率 |
|---------|------|---------|
| `weekly_digest` | 發送每週漫畫新出版清單給所有訂閱用戶 | 每週一次 |

### **任務執行流程**

```
1. 偵測過去 7 天內的新出版漫畫
2. 取得所有 active 用戶的郵件地址
3. 渲染 HTML 郵件模板
4. 發送郵件給每位用戶
5. 記錄執行結果和錯誤
```

---

## 🏠 本機測試

### **方法 1：使用 Django Management Command**

最簡單的測試方式：

```bash
# 進入 WSL 終端機
cd /path/to/ComicChase  # Replace with your project path

# 執行每週摘要郵件任務
python app/src/manage.py run_scheduled_email --task weekly_digest
```

**預期輸出：**

```bash
================================================================================
Cloud Run Email Notification Job
================================================================================
Task: weekly_digest
Started: 2026-01-13 22:45:00 CST
================================================================================
📧 Running weekly digest email notification...
=== Starting scheduled task: weekly_digest ===
[sync-execution] Starting weekly notification flow (sync=True)
[sync-execution] Found 15 new volumes to notify
[sync-execution] Found 3 active users
[sync-execution] Email sent to user1@example.com (1/3)
[sync-execution] Email sent to user2@example.com (2/3)
[sync-execution] Email sent to user3@example.com (3/3)
[sync-execution] Completed: {'task_id': 'sync-execution', 'status': 'completed', ...}
✅ Result: {'task_id': 'sync-execution', 'status': 'completed', ...}
=== Completed scheduled task: weekly_digest ===
================================================================================
✅ Email Notification Job Completed
Finished: 2026-01-13 22:46:30 CST
Duration: 90.00 seconds
================================================================================
```

---

### **方法 2：使用 Shell 腳本**

模擬 Cloud Run Jobs 的執行方式：

```bash
# 在 WSL 終端機
cd /path/to/ComicChase  # Replace with your project path

# 設定環境變數並執行
export EMAIL_TASK=weekly_digest
bash app/src/run_email.sh

# 或一行執行
EMAIL_TASK=weekly_digest ./run_email.sh
```

---

### **方法 3：在 Django Shell 中測試**

直接測試 Python 函數：

```bash
python app/src/manage.py shell
```

```python
from subscriptions.tasks import run_weekly_notification_flow

# Option 1: Use apply() for synchronous execution with task context
result = run_weekly_notification_flow.apply(kwargs={"sync": True})
print(result.result)

# Option 2: If you need truly direct invocation, the task handles missing self.request gracefully
# (falls back to "sync-execution" task_id), so current docs may still work
```

---

### **方法 4：測試單一郵件發送**

```python
from subscriptions.tasks import send_single_email_task

volumes_data = [
    {
        "title": "測試漫畫",
        "volume_number": 1,
        "region": "台灣",
        "release_date": "2026-01-13",
        "image_url": "https://example.com/image.jpg"
    }
]

# 測試發送到單一郵箱
result = send_single_email_task.apply(kwargs={
    "user_email": "test@example.com",
    "volumes_data": volumes_data,
    "sync": True
}).result
print(result)
```

---

## ☁️ Cloud Run Jobs 部署

### **前置準備**

確保已完成基礎設置：

```bash
# 設定環境變數
PROJECT_ID=$(gcloud config get-value core/project)
REGION=ap-northeast-1
SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
    --filter cloudrun-serviceaccount --format "value(email)")
IMAGE=${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service
```

---

### **Step 1: 建立 Cloud Run Job**

創建用於執行郵件通知的 Cloud Run Job：

```bash
# 建立 weekly_digest Job
gcloud run jobs create email-weekly-digest-job \
  --image ${IMAGE} \
  --region ${REGION} \
  --service-account ${SERVICE_ACCOUNT} \
  --set-env-vars EMAIL_TASK=weekly_digest \
  --set-cloudsql-instances ${PROJECT_ID}:${REGION}:${INSTANCE_NAME} \
  --set-secrets APPLICATION_SETTINGS=application_settings:latest \
  --memory 512Mi \
  --cpu 1 \
  --max-retries 2 \
  --task-timeout 30m \
  --command bash \
  --args /code/app/src/run_email.sh
```

**參數說明：**

- `--image`: 使用與 Web Service 相同的 Docker Image
- `--set-env-vars EMAIL_TASK=weekly_digest`: 設定要執行的任務
- `--set-cloudsql-instances`: 連接到 Cloud SQL 數據庫
- `--set-secrets`: 載入 Django 應用程式設定
- `--memory 512Mi`: 分配 512MB 記憶體（郵件任務不需太多資源）
- `--cpu 1`: 1 個 vCPU
- `--max-retries 2`: 失敗時最多重試 2 次
- `--task-timeout 30m`: 任務超時時間 30 分鐘
- `--command bash --args /code/app/src/run_email.sh`: 執行 shell 腳本

---

### **Step 2: 手動測試 Cloud Run Job**

在設置排程之前，先手動執行測試：

```bash
# 手動執行 Job
gcloud run jobs execute email-weekly-digest-job --region ${REGION}

# 查看執行狀態
gcloud run jobs executions list \
  --job email-weekly-digest-job \
  --region ${REGION}
```

**預期輸出：**

```bash
EXECUTION                                    STATUS     STARTED              COMPLETED            DURATION
email-weekly-digest-job-abc123              Succeeded  2026-01-13 14:00:00  2026-01-13 14:02:30  2m30s
```

---

### **Step 3: 查看執行日誌**

```bash
# 查看 Job 日誌
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=email-weekly-digest-job" \
  --limit 50 \
  --format "table(timestamp, textPayload)"
```

**預期日誌內容：**

```
TIMESTAMP                      TEXT_PAYLOAD
2026-01-13T14:00:00.000Z      ==========================================
2026-01-13T14:00:00.100Z      Cloud Run Email Notification Job
2026-01-13T14:00:00.200Z      ==========================================
2026-01-13T14:00:00.300Z      Task: weekly_digest
2026-01-13T14:00:00.400Z      Started: 2026-01-13 22:00:00 CST
2026-01-13T14:00:05.000Z      📧 Running weekly digest email notification...
2026-01-13T14:00:10.000Z      [sync-execution] Found 15 new volumes to notify
2026-01-13T14:00:11.000Z      [sync-execution] Found 3 active users
2026-01-13T14:00:30.000Z      [sync-execution] Email sent to user@example.com (1/3)
...
2026-01-13T14:02:28.000Z      ✅ Email Notification Job Completed
```

---

## ⏰ Cloud Scheduler 設置

### **創建定期排程**

設置每週自動執行郵件通知：

```bash
# 創建 Cloud Scheduler Job
# 每週一早上 9:00 發送（台北時間）
gcloud scheduler jobs create http email-weekly-digest-schedule \
  --location ${REGION} \
  --schedule "0 9 * * 1" \
  --time-zone "Asia/Taipei" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/email-weekly-digest-job:run" \
  --http-method POST \
  --oauth-service-account-email ${SERVICE_ACCOUNT}
```

**Cron 格式說明：**

- `0 9 * * 1` = 每週一早上 9:00
- 時區：`Asia/Taipei` (UTC+8)

**其他常用排程範例：**

```bash
# 每天早上 8:00
--schedule "0 8 * * *"

# 每週五下午 6:00
--schedule "0 18 * * 5"

# 每月 1 號早上 10:00
--schedule "0 10 1 * *"
```

參考：[Cron 格式線上工具](https://crontab.guru/)

---

### **手動觸發排程（測試）**

不等到排定時間，立即測試排程：

```bash
# 手動觸發
gcloud scheduler jobs run email-weekly-digest-schedule --location ${REGION}

# 查看排程狀態
gcloud scheduler jobs describe email-weekly-digest-schedule --location ${REGION}
```

---

### **查看排程執行歷史**

```bash
gcloud logging read \
  "resource.type=cloud_scheduler_job AND resource.labels.job_name=email-weekly-digest-schedule" \
  --limit 10 \
  --format "table(timestamp, httpRequest.status, textPayload)"
```

---

## 📊 監控與維護

### **1. 查看所有郵件相關 Jobs**

```bash
# 列出所有 Cloud Run Jobs
gcloud run jobs list --region ${REGION} | grep email

# 查看特定 Job 詳細資訊
gcloud run jobs describe email-weekly-digest-job --region ${REGION}
```

---

### **2. 查看所有郵件相關 Schedulers**

```bash
# 列出所有 Cloud Scheduler Jobs
gcloud scheduler jobs list --location ${REGION} | grep email

# 查看特定 Scheduler 詳細資訊
gcloud scheduler jobs describe email-weekly-digest-schedule --location ${REGION}
```

---

### **3. 檢查郵件發送狀態（AWS SES）**

```bash
# 使用 AWS CLI 查看 SES 發送統計
aws ses get-send-statistics --region us-east-1

# 查看最近的發送記錄
aws ses list-verified-email-addresses --region us-east-1
```

在 AWS Console 查看詳細資訊：
- **SES Dashboard**: https://console.aws.amazon.com/ses/
- **CloudWatch Metrics**: 監控發送成功率、退信率等

---

### **4. 設定失敗通知**

使用 Cloud Monitoring 設定 Alert Policy：

1. 前往 **Cloud Console** → **Monitoring** → **Alerting**
2. 點擊 **Create Policy**
3. 設定條件：
   - **Resource Type**: Cloud Run Job
   - **Metric**: Execution Status
   - **Filter**: `job_name = "email-weekly-digest-job" AND status = "Failed"`
4. 設定通知渠道（Email, Slack 等）

---

## 💰 成本估算

### **Cloud Run Jobs 計費**

按**實際執行時間**計費：

- **CPU**: $0.00002400 / vCPU-second
- **記憶體**: $0.00000250 / GiB-second

### **範例計算（每週執行 1 次）**

假設每次執行 5 分鐘 = 300 秒：

- 使用 1 vCPU + 512 MiB (0.5 GiB) 記憶體
- 每月執行 4 次

**成本：**

- CPU: 4 × 300 × 1 × $0.00002400 = **$0.03**
- 記憶體: 4 × 300 × 0.5 × $0.00000250 = **$0.0015**
- **月總計: ~$0.03 USD**

### **Cloud Scheduler 計費**

- **免費額度**: 每月 3 個 jobs 免費
- 郵件通知只有 1 個 scheduler → **免費**

### **AWS SES 計費**

假設每週發送 100 封郵件：

- 每月發送 ~400 封
- **免費額度**: 每月 62,000 封（如果從 EC2/Cloud Run 發送）
- **成本**: $0.00 USD（在免費額度內）

### **總計**

**預估每月成本: ~$0.03 USD** （幾乎可忽略）

---

## 🔧 故障排除

### **問題 1: Job 執行失敗（Exit Code 1）**

**可能原因：**

- 環境變數 `EMAIL_TASK` 未正確設定
- Cloud SQL 連線失敗
- AWS SES 配置錯誤
- 郵件模板渲染失敗

**解決方法：**

```bash
# 查看詳細錯誤日誌
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=email-weekly-digest-job AND severity>=ERROR" \
  --limit 20 \
  --format json
```

---

### **問題 2: 郵件未發送**

**檢查步驟：**

1. **確認 AWS SES 設定**

```bash
# 檢查 SES 驗證狀態
aws ses get-identity-verification-attributes \
  --identities your-verified-email@example.com \
  --region us-east-1

# 檢查 SES 是否在沙盒模式
aws ses get-account-sending-enabled --region us-east-1
```

2. **查看 Django 日誌**

```bash
gcloud logging read \
  "resource.type=cloud_run_job AND textPayload=~'SES Send Error'" \
  --limit 20
```

3. **檢查收件人郵箱**

- 檢查垃圾郵件資料夾
- 確認收件人郵箱有效

---

### **問題 3: Scheduler 未觸發 Job**

**檢查步驟：**

```bash
# 1. 確認 Scheduler 是否啟用
gcloud scheduler jobs describe email-weekly-digest-schedule --location ${REGION}

# 2. 查看 Scheduler 執行歷史
gcloud logging read \
  "resource.type=cloud_scheduler_job AND resource.labels.job_name=email-weekly-digest-schedule" \
  --limit 10
```

---

### **問題 4: 記憶體不足（OOM Killed）**

**症狀：** Job 在執行中途突然停止，Exit Code 137

**解決方法：** 增加記憶體配置

```bash
# 提升記憶體從 512Mi 到 1Gi
gcloud run jobs update email-weekly-digest-job \
  --region ${REGION} \
  --memory 1Gi
```

---

### **問題 5: 任務執行時間過長**

**可能原因：** 收件人數量過多

**解決方法：**

1. **增加 timeout 時間**

```bash
gcloud run jobs update email-weekly-digest-job \
  --region ${REGION} \
  --task-timeout 60m
```

2. **批次發送**：修改 `subscriptions/tasks.py` 實現批次發送

---

## 📝 定期維護檢查清單

### **每週檢查**

- [ ] 查看 Cloud Run Jobs 執行狀態
- [ ] 檢查是否有失敗的執行
- [ ] 驗證用戶是否收到郵件
- [ ] 檢查 AWS SES 發送統計

### **每月檢查**

- [ ] 檢閱 Cloud Logging 錯誤日誌
- [ ] 監控成本使用情況
- [ ] 更新 Docker Image（如有程式碼修改）
- [ ] 檢查 AWS SES 配額使用情況

### **更新 Docker Image 流程**

```bash
# 1. 建置新 Image
docker build -f app/Dockerfile \
  -t ${IMAGE} .

# 2. 推送到 Artifact Registry
docker push ${IMAGE}

# 3. 更新 Cloud Run Job
gcloud run jobs update email-weekly-digest-job \
  --image ${IMAGE} \
  --region ${REGION}

# 4. 手動測試執行
gcloud run jobs execute email-weekly-digest-job --region ${REGION}
```

---

## 🎯 總結

### **架構優勢**

✅ **完全獨立運行**
- Cloud Run Jobs 與 Web Service 完全分離
- 即使 Web Service scale to zero，郵件仍準時發送

✅ **成本極低**
- 按實際執行時間計費
- 預估每月 ~$0.03 USD

✅ **零維護**
- 無需管理 Celery Worker
- Google Cloud 負責基礎設施管理

✅ **高可靠性**
- 自動重試機制
- Cloud Logging 完整記錄

✅ **易於擴展**
- 需要新增郵件任務？只需創建新 Job 和 Scheduler

### **定時排程總覽**

| 郵件任務 | 頻率 | Cron | 執行時間（台北） | 預估執行時長 |
| -------- | ---- | ---- | --------------- | ----------- |
| **每週摘要** | 每週 | "0 12 * * 5" | 週五 12:00 | ~5 分鐘 |

---

## 📚 參考資料

- [Cloud Run Jobs 官方文件](https://cloud.google.com/run/docs/create-jobs)
- [Cloud Scheduler 官方文件](https://cloud.google.com/scheduler/docs)
- [AWS SES 官方文件](https://docs.aws.amazon.com/ses/)
- [Cron 格式參考](https://crontab.guru/)
- [Django Email 文件](https://docs.djangoproject.com/en/stable/topics/email/)

---

**文件版本：** 1.0
**最後更新：** 2026-01-13
**作者：** ComicChase Development Team

# 郵件通知定期任務 - 快速參考

本文檔提供郵件通知定期任務的快速參考指令。

---

## 🚀 快速開始

### **本機測試（推薦）**

```bash
# 在 WSL 終端機執行
cd /path/to/ComicChase  # Replace with your project path

# 方法 1: Django Management Command
python app/src/manage.py run_scheduled_email --task weekly_digest

# 方法 2: Shell 腳本
EMAIL_TASK=weekly_digest bash app/src/run_email.sh
```

---

## 📧 可用的郵件任務

| 任務名稱 | 說明 | 建議頻率 |
| --------- | ------ | --------- |
| `weekly_digest` | 發送每週漫畫新出版清單 | 每週一次 |
| `test_email` | 發送測試郵件 | 手動執行 |

---

## ☁️ Cloud Run Jobs 部署

### **建立 Cloud Run Job**

```bash
# 設定環境變數
PROJECT_ID=$(gcloud config get-value core/project)
REGION=us-central1
SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter cloudrun-serviceaccount --format "value(email)")
IMAGE=${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service
INSTANCE_NAME=comic-instance

# 建立 Job
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

# 手動測試
gcloud run jobs execute email-weekly-digest-job --region ${REGION}
```

---

### **建立 Cloud Scheduler**

```bash
# 每週五中午 12:00 發送（台北時間）
gcloud scheduler jobs create http email-weekly-digest-schedule \
  --location ${REGION} \
  --schedule "0 12 * * 5" \
  --time-zone "Asia/Taipei" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/email-weekly-digest-job:run" \
  --http-method POST \
  --oauth-service-account-email ${SERVICE_ACCOUNT}

# 手動觸發測試
gcloud scheduler jobs run email-weekly-digest-schedule --location ${REGION}
```

---

## 📊 監控指令

### **查看 Job 狀態**

```bash
# 列出所有執行記錄
gcloud run jobs executions list --job email-weekly-digest-job --region ${REGION}

# 查看最新執行狀態
gcloud run jobs executions describe $(gcloud run jobs executions list --job email-weekly-digest-job --region ${REGION} --format="value(name)" --limit=1) --region ${REGION}
```

---

## 📨 發送測試郵件

### **透過 Cloud Run Job 發送**

```bash
# 發送測試郵件到指定郵箱
gcloud run jobs execute email-weekly-digest-job \
  --region ${REGION} \
  --update-env-vars "EMAIL_TASK=test_email,TEST_EMAIL_TO=your@email.com"

# 查看日誌
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=email-weekly-digest-job" \
  --limit 20 \
  --format "table(timestamp, textPayload)"
```

### **本機發送**

```bash
python app/src/manage.py send_test_email --to your@email.com
```

---

### **查看日誌**

```bash
# 查看 Job 日誌
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=email-weekly-digest-job" \
  --limit 50 \
  --format "table(timestamp, textPayload)"

# 查看錯誤日誌
gcloud logging read \
  "resource.type=cloud_run_job AND resource.labels.job_name=email-weekly-digest-job AND severity>=ERROR" \
  --limit 20
```

---

### **查看 Scheduler 狀態**

```bash
# 查看 Scheduler 詳細資訊
gcloud scheduler jobs describe email-weekly-digest-schedule --location ${REGION}

# 查看執行歷史
gcloud logging read \
  "resource.type=cloud_scheduler_job AND resource.labels.job_name=email-weekly-digest-schedule" \
  --limit 10
```

---

## 🔧 管理指令

### **更新 Job**

```bash
# 更新 Image
gcloud run jobs update email-weekly-digest-job \
  --image ${IMAGE} \
  --region ${REGION}

# 更新記憶體
gcloud run jobs update email-weekly-digest-job \
  --region ${REGION} \
  --memory 1Gi

# 更新 timeout
gcloud run jobs update email-weekly-digest-job \
  --region ${REGION} \
  --task-timeout 60m
```

---

### **暫停/恢復 Scheduler**

```bash
# 暫停排程
gcloud scheduler jobs pause email-weekly-digest-schedule --location ${REGION}

# 恢復排程
gcloud scheduler jobs resume email-weekly-digest-schedule --location ${REGION}
```

---

### **刪除資源**

```bash
# 刪除 Scheduler（先暫停）
gcloud scheduler jobs pause email-weekly-digest-schedule --location ${REGION}
gcloud scheduler jobs delete email-weekly-digest-schedule --location ${REGION}

# 刪除 Job
gcloud run jobs delete email-weekly-digest-job --region ${REGION}
```

---

## 🐛 故障排除

### **檢查 AWS SES 狀態**

```bash
# 查看已驗證的郵箱
aws ses list-verified-email-addresses --region us-east-1

# 查看發送統計
aws ses get-send-statistics --region us-east-1
```

---

### **測試郵件發送**

```python
# Django shell
python app/src/manage.py shell

from subscriptions.tasks import send_single_email_task

volumes_data = [
    {
        "title": "測試漫畫",
        "volume_number": 1,
        "region": "台灣",
        "release_date": "2026-01-13",
        "image_url": "https://via.placeholder.com/300x400"
    }
]

send_single_email_task(
    None,
    user_email="your-verified-email@example.com",
    volumes_data=volumes_data,
    sync=True
)
```

---

## 📚 完整文檔

- **詳細部署指南**: [email-notification-scheduler.md](./email-notification-scheduler.md)
- **本機測試指南**: [email-notification-local-testing-guide.md](./email-notification-local-testing-guide.md)
- **後端部署**: [cloud-backend.md](./cloud-backend.md)

---

**快速參考版本：** 1.0
**最後更新：** 2026-01-13

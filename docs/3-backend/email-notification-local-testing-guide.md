# 郵件通知任務本機測試指南

本文檔提供詳細的本機測試步驟，確保在部署到 Cloud Run 之前，郵件通知功能正常運作。

---

## 📋 測試前準備

### **1. 確認環境配置**

檢查 `.env` 文件中的 AWS SES 設定：

```bash
# 查看環境變數
cat .env | grep AWS
```

確保包含以下設定：

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

---

### **2. 確認 AWS SES 驗證狀態**

```bash
# 檢查已驗證的郵箱
aws sesv2 list-email-identities --region ap-northeast-1

```

**重要：** 如果 AWS SES 在沙盒模式，只能發送郵件到已驗證的郵箱。

---

### **3. 確認有測試用戶**

```python
from django.contrib.auth import get_user_model

User = get_user_model()

# 檢查 active 用戶
active_users = User.objects.filter(is_active=True)
print(f"找到 {active_users.count()} 位 active 用戶")

# 查看用戶郵箱
for user in active_users:
    print(f"- {user.email}")

# 如果沒有測試用戶，創建一個
if active_users.count() == 0:
    User.objects.create_user(
        username='testuser',
        email='your-verified-email@example.com',  # 使用 AWS SES 已驗證的郵箱
        password='testpass123',
        is_active=True
    )
    print("✅ 已創建測試用戶")
```

---

## 🧪 測試方法

### **測試 1：Django Management Command**

最簡單直接的測試方式。

#### **在 WSL 終端機執行**

```bash
cd /path/to/ComicChase  # Replace with your project path

# 執行郵件任務
python app/src/manage.py run_scheduled_email --task weekly_digest
```

#### **預期輸出**

```bash
================================================================================
Cloud Run Email Notification Job
================================================================================
Task: weekly_digest
Started: 2026-01-13 22:50:00 CST
================================================================================
📧 Running weekly digest email notification...
=== Starting scheduled task: weekly_digest ===
[sync-execution] Starting weekly notification flow (sync=True)
[sync-execution] Found 1 new volumes to notify
[sync-execution] Found 1 active users
[sync-execution] Rendering template for test@example.com with 1 items
[sync-execution] Email sent successfully to test@example.com
[sync-execution] Email sent to test@example.com (1/1)
[sync-execution] Completed: {'task_id': 'sync-execution', 'status': 'completed', ...}
✅ Result: {'task_id': 'sync-execution', 'status': 'completed', ...}
=== Completed scheduled task: weekly_digest ===
================================================================================
✅ Email Notification Job Completed
Finished: 2026-01-13 22:50:30 CST
Duration: 30.00 seconds
================================================================================
```

#### **檢查郵箱**

- 登入收件人郵箱（AWS SES 已驗證的郵箱）
- 檢查收件匣或垃圾郵件資料夾
- 確認收到「【ComicChase】本週漫畫新出版清單」郵件

---

### **測試 2：Shell 腳本**

模擬 Cloud Run Jobs 的執行環境。

#### **執行步驟**

```bash
cd /path/to/ComicChase  # Replace with your project path

# 賦予執行權限（如果需要）
chmod +x app/src/run_email.sh

# 使用環境變數執行
export EMAIL_TASK=weekly_digest
bash app/src/run_email.sh

# 或一行執行
EMAIL_TASK=weekly_digest bash app/src/run_email.sh
```

##### 預期輸出

```bash
===========================================
Starting Email Notification Task
===========================================
Task: weekly_digest
Time: Mon Jan 13 22:50:00 CST 2026
===========================================
================================================================================
Cloud Run Email Notification Job
================================================================================
...（同上）
===========================================
✅ Email Task Completed Successfully
Task: weekly_digest
Time: Mon Jan 13 22:50:30 CST 2026
===========================================
```

---

### **測試 3：Python 函數直接調用**

在 Django shell 中測試核心功能。

#### **Step 1: 進入 Django Shell**

```bash
python app/src/manage.py shell
```

#### **Step 2: 測試同步執行**

```python
from subscriptions.tasks import run_weekly_notification_flow

# 同步執行（模擬 Cloud Run Jobs）
result = run_weekly_notification_flow(sync=True)
print(result)
```

**預期結果：**

```python
{
    'task_id': 'sync-execution',
    'status': 'completed',
    'total_recipients': 1,
    'success_count': 1,
    'failed_count': 0,
    'volumes_count': 1
}
```

#### **Step 3: 測試異步執行（需要 Celery Worker）**

```python
# 異步執行（使用 Celery）
result = run_weekly_notification_flow(sync=False)
print(result)
```

**預期結果：**

```python
{
    'task_id': 'abc-123-def',  # Celery task ID
    'status': 'dispatched',
    'total_recipients': 1,
    'volumes_count': 1
}
```

**注意：** 異步執行需要 Celery Worker 運行：

```bash
# 在另一個終端機啟動 Celery Worker
cd /path/to/ComicChase  # Replace with your project path
celery -A config worker -l info
```

---

### **測試 4：測試單一郵件發送**

測試郵件渲染和發送功能。

#### **在 Django Shell 執行**

```python
from subscriptions.tasks import send_single_email_task

# 準備測試資料
volumes_data = [
    {
        "title": "測試漫畫",
        "volume_number": 1,
        "region": "台灣",
        "release_date": "2026-01-13",
        "image_url": "https://via.placeholder.com/300x400"
    },
    {
        "title": "Another Test Comic",
        "volume_number": 5,
        "region": "日本",
        "release_date": "2026-01-12",
        "image_url": "https://via.placeholder.com/300x400"
    }
]

# 發送測試郵件（直接調用，不通過 Celery）
result = send_single_email_task(
    "your-verified-email@example.com",  # user_email - 使用 AWS SES 已驗證的郵箱
    volumes_data,  # volumes_data
    sync=True  # sync
)
print(result)
```

**預期輸出：**

```bash
Email sent to your-verified-email@example.com
```

---

### **測試 5：測試無新書情況**

測試當沒有新書時的郵件內容。

```python
from subscriptions.tasks import send_single_email_task

# 空資料
volumes_data = []

# 發送測試郵件（直接調用，不通過 Celery）
result = send_single_email_task(
    "your-verified-email@example.com",
    volumes_data,
    sync=True
)
print(result)
```

**預期：** 收到標題為「【ComicChase】本週無新刊出版通知」的郵件

---

## 🔍 測試檢查清單

執行本機測試時，請確認以下項目：

### **基本功能測試**

- [ ] `python manage.py run_scheduled_email --task weekly_digest` 執行成功
- [ ] `EMAIL_TASK=weekly_digest bash run_email.sh` 執行成功
- [ ] 郵件成功發送到測試用戶
- [ ] 郵件內容正確顯示（HTML 格式）
- [ ] 郵件圖片正常顯示
- [ ] 無新書時發送正確的通知郵件

### **資料正確性測試**

- [ ] 正確偵測過去 7 天的新書
- [ ] 正確取得所有 active 用戶
- [ ] Volume 資料正確傳遞到模板
- [ ] 日期格式正確

### **錯誤處理測試**

- [ ] 錯誤的任務名稱會正確報錯
- [ ] AWS SES 錯誤時有適當的錯誤訊息
- [ ] 資料庫連線失敗時有錯誤訊息

### **向後兼容測試**

- [ ] 原有的 Celery 非同步執行仍然正常（`sync=False`）
- [ ] 與現有的爬蟲任務整合正常

---

## 🐛 常見問題排除

### **問題 1: 郵件未發送**

**症狀：** 任務執行成功，但未收到郵件

**檢查步驟：**

1. **檢查 AWS SES 驗證狀態**

    ```bash
    aws ses get-identity-verification-attributes \
    --identities your-email@example.com \
    --region us-east-1
    ```

2. **檢查 AWS SES 沙盒模式**

    ```bash
    aws sesv2 get-account --region us-east-1
    ```

    如果在沙盒模式，只能發送到已驗證的郵箱。

3. **檢查收件人郵箱**

    - 檢查垃圾郵件資料夾
    - 確認郵箱地址正確

4. **查看詳細錯誤日誌**

    ```bash
    # 在執行任務時查看 Django 日誌
    python app/src/manage.py run_scheduled_email --task weekly_digest --verbosity 2
    ```

---

### **問題 2: HTML 郵件未渲染**

**症狀：** 郵件中有 `{{` 或 `{%` 標籤未被替換

**原因：** 模板路徑或變數傳遞問題

**解決方法：**

```python
# 在 Django shell 中測試模板渲染
from django.template.loader import render_to_string

volumes_data = [
    {
        "title": "測試",
        "volume_number": 1,
        "region": "台灣",
        "release_date": "2026-01-13",
        "image_url": "https://example.com/image.jpg"
    }
]

html_content = render_to_string(
    "emails/weekly_digest.html",
    {"volumes": volumes_data, "site_url": "https://comicchase.web.app"}
)

print(html_content)

# 檢查是否還有未渲染的標籤
if "{{" in html_content or "{%" in html_content:
    print("❌ 模板渲染失敗！")
else:
    print("✅ 模板渲染成功！")
```

---

### **問題 3: AWS Credentials 錯誤**

**症狀：**

```bash
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**解決方法：**

1. **檢查環境變數**

```bash
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY
```

1. **檢查 `.env` 文件**

```bash
cat .env | grep AWS
```

1. **重新載入環境變數**

```bash
# 如果使用 docker-compose
docker-compose down
docker-compose up -d

# 如果在本機虛擬環境
source venv/bin/activate
export $(cat .env | xargs)
```

---

### **問題 4: 圖片無法顯示**

**症狀：** 郵件中的漫畫圖片無法顯示

**原因：**

- 圖片 URL 無效
- 圖片需要認證
- 圖片連結已過期

**解決方法：**

```python
# 檢查圖片 URL
from comic.models import Volume

volumes = Volume.objects.all()[:5]
for v in volumes:
    print(f"{v.title}: {v.image_url}")

# 測試圖片 URL 是否可訪問
import requests
response = requests.get(v.image_url)
print(f"Status: {response.status_code}")
```

**建議：** 使用 CDN 托管的圖片或確保圖片 URL 永久有效

---

### **問題 5: 資料庫連線失敗**

**症狀：**

```bash
django.db.utils.OperationalError: could not connect to server
```

**解決方法：**

```bash
# 檢查資料庫是否運行
docker-compose ps db

# 重啟資料庫
docker-compose restart db

# 測試資料庫連線
python app/src/manage.py dbshell
```

---

## 📝 測試完成後的檢查

### **1. 驗證同步執行模式**

```python
# Django shell
from subscriptions.tasks import run_weekly_notification_flow
import inspect

sig = inspect.signature(run_weekly_notification_flow)
print(sig)
# 應該顯示: (self, sync=False)
```

### **2. 驗證原有 Celery 模式仍然正常**

```bash
# 啟動 Celery Worker
celery -A config worker -l info

# 在另一個終端執行
python app/src/manage.py shell
```

```python
from subscriptions.tasks import run_weekly_notification_flow

# Celery 異步執行
result = run_weekly_notification_flow.delay()
print(result.id)  # 應該返回 task ID
```

### **3. 檢查郵件內容**

- [ ] 主旨正確
- [ ] HTML 格式正確
- [ ] 漫畫資訊完整（標題、集數、地區、發售日期）
- [ ] 圖片正常顯示
- [ ] 連結正確（如果有）
- [ ] 排版美觀

### **4. 檢查日誌**

```bash
# 查看應用程式日誌
tail -f app/src/logs/*.log

# 或查看 Docker 日誌
docker-compose logs -f web
```

---

## ✅ 測試通過標準

在部署到雲端之前，確保以下測試都通過：

### 基本功能測試

- [ ] `python manage.py run_scheduled_email --task weekly_digest` 執行成功
- [ ] `EMAIL_TASK=weekly_digest bash run_email.sh` 執行成功
- [ ] 郵件成功發送並收到

### 資料完整性測試

- [ ] 正確偵測新書資料
- [ ] 正確取得用戶列表
- [ ] 郵件內容正確渲染

### 向後兼容測試

- [ ] 原有的 Celery 非同步執行仍然正常
- [ ] 與爬蟲任務整合正常

---

## 🚀 測試通過後的下一步

當所有本機測試都通過後，您可以：

1. **提交程式碼**

   ```bash
   git add .
   git commit -m "Add email notification scheduler with Cloud Run Jobs support"
   git push
   ```

2. **建置 Docker Image**

   ```bash
   docker build -f app/Dockerfile \
     -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/comicchase-service .
   ```

3. **部署到 Cloud Run Jobs**（參考 `email-notification-scheduler.md`）

---

## 📚 相關文件

- [email-notification-scheduler.md](./email-notification-scheduler.md) - 雲端部署完整指南
- [cloud-backend-crawler-run-jobs-scheduler.md](./cloud-backend-crawler-run-jobs-scheduler.md) - 爬蟲任務參考
- [Project README](../../README.md) - 專案總覽

---

**文件版本：** 1.0
**最後更新：** 2026-01-13
**作者：** ComicChase Development Team

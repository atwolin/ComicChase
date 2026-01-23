# 本機測試指南：Cloud Run Jobs 爬蟲任務

## 📋 文件目的

本文件說明如何在**本機環境**測試 Cloud Run Jobs 爬蟲任務，確保程式邏輯正確後再部署到雲端。

**最後更新：** 2026-01-06
**文件版本：** 1.0

---

## ✅ 可以在本機測試的項目

| 測試項目 | 本機可測試 | 說明 |
| --------- | ----------- | ------ |
| ✅ Management Command | 是 | `python manage.py run_scheduled_crawler` |
| ✅ Tasks.py 同步執行 | 是 | 直接呼叫 `tasks.crawl_all_series_eslite(sync=True)` |
| ✅ Shell 腳本邏輯 | 是 | 使用環境變數執行 `run_crawler.sh` |
| ✅ 資料庫寫入 | 是 | 連接本地資料庫測試 |
| ⚠️ Cloud SQL 連線 | 部分 | 可透過 Cloud SQL Proxy 測試 |
| ❌ Cloud Scheduler 觸發 | 否 | 需要 GCP 環境 |
| ❌ Cloud Run Jobs 執行 | 否 | 需要 GCP 環境 |

---

## 🧪 本機測試步驟

### **前置條件**

確保您的本機開發環境已設定：

```bash
# 1. 確認在專案根目錄
cd /path/to/ComicChase  # 替換為您的專案路徑

# 2. 確認 Docker Compose 環境正在運行
docker-compose ps

# 應該看到：
# - db (PostgreSQL)
# - rabbitmq
# - app (Django)
# - celery_worker
```

---

## 測試方法 1：直接測試 Management Command（推薦）

這是最簡單直接的測試方式。

### **Step 1: 進入 Django Container**

```bash
# 方法 A: 使用 docker-compose exec
docker-compose exec app bash

# 方法 B: 如果在本機虛擬環境
source venv/bin/activate  # 如果使用 venv
cd app/src
```

### **Step 2: 執行 Management Command**

```bash
# 測試 books.tw 每日新書爬蟲
python manage.py run_scheduled_crawler --task bookstw_new

# 測試 Eslite 所有系列爬蟲
python manage.py run_scheduled_crawler --task eslite_all_series

# 測試 Books.jp 所有系列爬蟲
python manage.py run_scheduled_crawler --task booksjp_all_series

# 測試 Eslite orphan volumes 爬蟲
python manage.py run_scheduled_crawler --task eslite_orphan_volumes
```

### **預期輸出**

```text
=== Starting scheduled task: bookstw_new ===
Starting synchronous crawl for books.com.tw
Crawling new releases...
[Scrapy 日誌...]
✅ Completed: bookstw_new
Result: {'total_tasks': 1, 'completed': 1}
```

### **驗證資料庫**

```bash
# 在 Django shell 中檢查
python manage.py shell

# 執行以下 Python 程式碼
>>> from comic.models import Volume, Series
>>>
>>> # 查看最新新增的 Volumes
>>> Volume.objects.order_by('-created_at')[:5]
>>>
>>> # 查看資料數量
>>> Volume.objects.count()
>>> Series.objects.count()
```

---

## 測試方法 2：測試 Shell 腳本

模擬 Cloud Run Jobs 的執行環境。

### **Step 1: 設定環境變數**

```bash
# 在 container 內
export CRAWLER_TASK=bookstw_new
export DJANGO_SETTINGS_MODULE=config.settings.local  # 本機使用 local settings
```

### **Step 2: 執行 Shell 腳本**

```bash
# 在 container 內
cd /code/app  # 或您的專案路徑
bash run_crawler.sh
```

#### 預期輸出

```text
=========================================
Cloud Run Crawler Job
=========================================
Task: bookstw_new
Started: 2026-01-06 23:42:00 CST
=========================================
📚 Running books.com.tw new releases crawler...
=== Starting scheduled task: bookstw_new ===
[執行過程...]
✅ Completed: bookstw_new
=========================================
✅ Crawler Job Completed
Finished: 2026-01-06 23:57:00 CST
=========================================
```

### **測試所有任務**

```bash
# 測試 Orphan Volumes
export CRAWLER_TASK=eslite_orphan_volumes
bash run_crawler.sh

# 測試 Eslite
export CRAWLER_TASK=eslite_all_series
bash run_crawler.sh

# 測試 Books.jp
export CRAWLER_TASK=booksjp_all_series
bash run_crawler.sh

# 測試錯誤處理
export CRAWLER_TASK=invalid_task
bash run_crawler.sh
# 預期輸出：❌ Error: Unknown CRAWLER_TASK: invalid_task
```

---

## 測試方法 3：直接測試 Python 函數

在 Django shell 或 Python script 中測試。

### **Step 1: 進入 Django Shell**

```bash
python manage.py shell
```

### **Step 2: 測試同步執行**

```python
from comic_scrapers import tasks

# 測試 books.tw 新書爬蟲
result = tasks.crawl_new_volumes_bookstw(sync=True)
print(result)

# 測試 Eslite 所有系列
result = tasks.crawl_all_series_eslite(sync=True)
print(result)

# 測試 Books.jp 所有系列
result = tasks.crawl_all_series_booksjp(sync=True)
print(result)

# 測試 Orphan Volumes
result = tasks.crawl_orphan_volumes_eslite(sync=True)
print(result)
```

### **Step 3: 驗證非同步執行（原有 Celery 邏輯）**

確保修改後仍然支援原有的 Celery 執行方式：

```python
from comic_scrapers import tasks

# 測試非同步執行（需要 Celery Worker 運行）
result = tasks.crawl_all_series_eslite(sync=False)
print(result)
# 應該返回: {'total_tasks': N, 'group_id': '...'}
```

---

## 測試方法 4：在本機 Docker Container 中完整模擬

完整模擬 Cloud Run Jobs 的執行環境。

### **Step 1: 建立測試腳本**

**檔案：** `test_crawler_job.sh`

```bash
#!/bin/bash
# 本機測試腳本：模擬 Cloud Run Jobs 執行

set -e

echo "========================================="
echo "Local Test: Cloud Run Crawler Job"
echo "========================================="

# 測試所有任務
TASKS=("bookstw_new" "eslite_all_series" "booksjp_all_series" "eslite_orphan_volumes")

for task in "${TASKS[@]}"; do
    echo ""
    echo "Testing task: ${task}"
    echo "-----------------------------------------"

    export CRAWLER_TASK=$task
    export DJANGO_SETTINGS_MODULE=config.settings.local

    # 執行測試（設定短 timeout 避免爬取太久）
    timeout 30s bash app/src/run_crawler.sh || {
        if [ $? -eq 124 ]; then
            echo "⏱️  Timeout (expected for long tasks)"
        else
            echo "❌ Task failed: ${task}"
            exit 1
        fi
    }

    echo "✅ Task started successfully: ${task}"
done

echo ""
echo "========================================="
echo "✅ All tasks tested successfully"
echo "========================================="
```

### **Step 2: 執行測試**

```bash
# 賦予執行權限
chmod +x test_crawler_job.sh

# 執行測試
./test_crawler_job.sh
```

---

## 🔍 測試檢查清單

執行本機測試時，請確認以下項目：

### **功能測試**

- [ ] `run_scheduled_crawler.py` 可正確執行
- [ ] 所有 4 個任務（bookstw_new, eslite_all_series, booksjp_all_series, eslite_orphans）都能執行
- [ ] `run_crawler.sh` 腳本可正常運作
- [ ] 環境變數 `CRAWLER_TASK` 正確傳遞
- [ ] 錯誤的 `CRAWLER_TASK` 會正確報錯

### **資料庫測試**

- [ ] 爬蟲資料正確寫入資料庫
- [ ] `Series` 和 `Volume` 關聯正確
- [ ] 沒有重複資料

### **日誌測試**

- [ ] 日誌輸出清晰易讀
- [ ] 錯誤訊息有足夠的 debug 資訊
- [ ] 執行時間有記錄

### **錯誤處理測試**

- [ ] 錯誤的任務名稱會報錯並退出
- [ ] 爬蟲失敗時有適當的錯誤處理
- [ ] 資料庫連線失敗時有錯誤訊息

---

## 🐛 常見問題排除

### **問題 1: ModuleNotFoundError**

```text
ModuleNotFoundError: No module named 'comic_scrapers'
```

**原因：** Python path 設定問題

**解決方法：**

```bash
# 確保在正確的目錄
cd app/src

# 或設定 PYTHONPATH
export PYTHONPATH=/code/app/src:$PYTHONPATH
```

---

### **問題 2: 資料庫連線失敗**

```text
django.db.utils.OperationalError: could not connect to server
```

**原因：** 資料庫未啟動或設定錯誤

**解決方法：**

```bash
# 檢查資料庫是否運行
docker-compose ps db

# 重啟資料庫
docker-compose restart db

# 檢查資料庫設定
python manage.py dbshell
```

---

### **問題 3: Selenium WebDriver 錯誤**

```text
selenium.common.exceptions.WebDriverException: Chrome not found
```

**原因：** Chrome/ChromeDriver 未安裝

**解決方法：**

```bash
# 在 Docker container 內應該已經安裝
# 如果在本機虛擬環境，需要安裝 Chrome 和 ChromeDriver

# Ubuntu/Debian
sudo apt-get install chromium-browser chromium-chromedriver

# macOS
brew install --cask chromium
brew install chromedriver
```

---

### **問題 4: 任務執行時間過長**

**原因：** 爬取所有系列需要較長時間（特別是 eslite_all_series）

**解決方法（測試用）：**

暫時修改 `tasks.py` 限制爬取數量：

```python
# 在 crawl_all_series_eslite 中
series_list = Series.objects.filter(title_tw__isnull=False).values(
    "title_tw", "latest_volume_tw__release_date"
)[:5]  # 只爬取前 5 個系列進行測試
```

---

## 📝 測試完成後的檢查

### **1. 驗證同步執行模式**

```python
# Django shell
from comic_scrapers import tasks

# 確認有 sync 參數
import inspect
sig = inspect.signature(tasks.crawl_all_series_eslite)
print(sig)
# 應該顯示: (sync=False)
```

### **2. 驗證原有 Celery 模式仍然正常**

```bash
# 確保非同步模式（原有功能）沒有被破壞
python manage.py shell

>>> from comic_scrapers import tasks
>>> result = tasks.crawl_all_series_eslite.delay()  # Celery 方式
>>> result.id  # 應該返回 task ID
```

### **3. 檢查資料庫資料**

```bash
python manage.py shell

>>> from comic.models import Volume, Series
>>> from django.utils import timezone
>>> from datetime import timedelta
>>>
>>> # 檢查最近 1 小時內新增的資料
>>> one_hour_ago = timezone.now() - timedelta(hours=1)
>>> recent_volumes = Volume.objects.filter(created_at__gte=one_hour_ago)
>>> print(f"新增 {recent_volumes.count()} 個 Volumes")
>>>
>>> # 檢查最新的 Volume
>>> latest = Volume.objects.order_by('-created_at').first()
>>> print(f"最新 Volume: {latest.title_tw} ({latest.release_date_tw})")
```

---

## ✅ 測試通過標準

在部署到雲端之前，確保以下測試都通過：

### **基本功能測試**

- [ ] `python manage.py run_scheduled_crawler --task bookstw_new` 執行成功
- [ ] `python manage.py run_scheduled_crawler --task eslite_all_series` 執行成功
- [ ] `python manage.py run_scheduled_crawler --task booksjp_all_series` 執行成功
- [ ] `python manage.py run_scheduled_crawler --task eslite_orphan_volumes` 執行成功

### **Shell 腳本測試**

- [ ] `CRAWLER_TASK=bookstw_new bash run_crawler.sh` 執行成功
- [ ] 錯誤的任務名稱會正確報錯

### **資料完整性測試**

- [ ] 爬蟲資料正確寫入資料庫
- [ ] 沒有產生重複資料
- [ ] `Series` 和 `Volume` 關聯正確

### **向後兼容測試**

- [ ] 原有的 Celery 非同步執行仍然正常（`sync=False`）
- [ ] 現有的 management commands 仍然可用

---

## 🚀 測試通過後的下一步

當所有本機測試都通過後，您可以：

1. **提交程式碼**

   ```bash
   git add .
   git commit -m "Add Cloud Run Jobs scheduler support with sync execution mode"
   git push
   ```

2. **建置 Docker Image**

   ```bash
   docker build -f app/Dockerfile.gcr -t gcr.io/YOUR_PROJECT/comicchase-backend:latest .
   ```

3. **推送到 GCR**

   ```bash
   docker push gcr.io/YOUR_PROJECT/comicchase-backend:latest
   ```

4. **部署到 Cloud Run Jobs**（參考 `cloud-run-jobs-scheduler.md`）

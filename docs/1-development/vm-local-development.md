# 本地運行 VM 架構指南

本文件說明如何在本地環境使用 `docker-compose-vm.yaml` 運行模擬 Oracle Cloud VM 的完整後端架構，
以及過程中需要對程式碼進行的改動與原因。

---

## 背景

`deploy/change_to_vm` 分支將後端部署目標從 GCP Cloud Run 遷移至 Oracle Cloud VM。
在本地測試此架構時，會遇到以下三個問題：

1. **Gunicorn Worker 記憶體溢出 (OOM)**
2. **Django `ALLOWED_HOSTS` 不包含 `localhost`**
3. **Nginx 找不到 SSL 憑證導致無法啟動**

以下分別說明各問題的修改方式與理由。

---

## 1. Gunicorn Worker 數量調整

### 檔案

`app/src/config/gunicorn/gunicorn_config.py`

### 問題

原始設定使用 `multiprocessing.cpu_count() * 2 + 1` 動態計算 Worker 數量。
在本地開發機器上（通常 8–16 核心），這會產生 17–33 個 Worker，
但 `docker-compose-vm.yaml` 將 backend 容器的記憶體限制為 **512MB**，
導致 Worker 不斷被系統以 `SIGKILL` 強制終止，Nginx 轉發請求時收到 **502 Bad Gateway**。

### 修改內容

```diff
 # Worker processes
-workers = multiprocessing.cpu_count() * 2 + 1
+import os
+workers = int(os.environ.get('WEB_CONCURRENCY', 2))
```

### 說明

- 預設值改為 **2 個 Worker**，足以應付本地開發與測試需求，也能在 512MB 記憶體限制內穩定運行。
- 透過環境變數 `WEB_CONCURRENCY` 可自由調整，不影響線上部署彈性。
  例如在 Oracle Cloud VM 上可於 `.env.vm` 中設定 `WEB_CONCURRENCY=4`。

---

## 2. Django ALLOWED_HOSTS 加入 localhost

### 檔案

`app/src/config/settings/vm.py`

### 問題

`vm.py` 中 `ALLOWED_HOSTS` 寫死僅允許線上域名：

```python
ALLOWED_HOSTS = [
    "comicchase.site",
    "api.comicchase.site",
]
```

在本地以 `https://localhost` 存取時，Django 會回傳 **400 Bad Request**。
又因為 `DEBUG=False`，Django 會嘗試透過 AWS SES 將錯誤報告寄給 `ADMINS`，
而寄件地址未在 SES 中驗證，觸發連鎖 **500 Internal Server Error**。

### 修改內容

```diff
 ALLOWED_HOSTS = [
     "comicchase.site",
     "api.comicchase.site",
-]
+] + env.list("DJANGO_ALLOWED_HOSTS", default=[])
```

### 說明

- 保留原有線上域名，同時從環境變數 `DJANGO_ALLOWED_HOSTS` 讀取額外允許的 Host。
- 在本地的 `.env.vm` 中設定 `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` 即可。
- 線上環境不設此環境變數，行為不受影響（`default=[]`）。

---

## 3. 產生自我簽署 SSL 憑證（修復 Nginx 憑證問題）

### 問題

`docker-compose-vm.yaml` 中的 Nginx 容器掛載了 `app/src/ssl` 目錄，
並在 `default.conf.template` 中引用了以下憑證路徑：

```nginx
ssl_certificate      /code/app/ssl/fullchain.pem;
ssl_certificate_key  /code/app/ssl/privkey.pem;
```

在線上環境中，這些憑證由 **Certbot (Let's Encrypt)** 自動產生並放置。
但在本地開發環境中，`app/src/ssl/` 目錄是空的，導致 Nginx 啟動時報錯並不斷重啟：

```
nginx: [emerg] cannot load certificate "/code/app/ssl/fullchain.pem": BIO_new_file() failed
(SSL: error:80000002:system library::No such file or directory)
```

### 解決方式

使用 Docker 執行 `openssl` 指令，在 `app/src/ssl/` 目錄下產生一組**自我簽署憑證 (Self-Signed Certificate)**：

```bash
docker run --rm \
  -v ${PWD}/app/src/ssl:/ssl \
  alpine/openssl \
  req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout /ssl/privkey.pem \
  -out /ssl/fullchain.pem \
  -subj "/CN=localhost"
```

#### 指令參數說明

| 參數 | 說明 |
|------|------|
| `docker run --rm` | 用完即刪除容器，不留殘留 |
| `-v ${PWD}/app/src/ssl:/ssl` | 將本地的 `app/src/ssl` 掛載到容器內的 `/ssl`，讓產生的憑證直接寫入本地 |
| `alpine/openssl` | 使用輕量級的 Alpine OpenSSL 映像檔，無需在本機安裝 OpenSSL |
| `req -x509` | 產生自我簽署的 X.509 憑證（非 CSR） |
| `-nodes` | 不對私鑰加密（No DES），避免啟動 Nginx 時需要輸入密碼 |
| `-days 365` | 憑證有效期 365 天，足夠本地開發使用 |
| `-newkey rsa:2048` | 同時產生一把 2048-bit RSA 私鑰 |
| `-keyout /ssl/privkey.pem` | 私鑰輸出路徑 |
| `-out /ssl/fullchain.pem` | 憑證輸出路徑 |
| `-subj "/CN=localhost"` | 設定憑證的 Common Name 為 `localhost`，跳過互動式問答 |

### 為什麼使用自我簽署憑證？

1. **Nginx 必須有憑證才能啟動**：`default.conf.template` 設定了 `listen 443 ssl`，
   如果找不到 `fullchain.pem` 和 `privkey.pem`，Nginx 會直接拒絕啟動。
2. **本地無法取得正式憑證**：Let's Encrypt 需要公開可達的域名驗證，`localhost` 不符合條件。
3. **自我簽署憑證足以測試**：雖然瀏覽器會顯示「不安全」警告，但 HTTPS 加密通道本身是正常運作的，
   對測試 API 和 Admin 後台不產生影響，點擊「繼續前往」即可。

> ⚠️ **注意**：`app/src/ssl/` 目錄已被加入 `.gitignore`，產生的憑證不會被提交到版本控制中。
> 每位開發者在本地首次啟動 VM 架構時，都需要執行一次上述指令。

---

## 完整本地啟動流程

```bash
# 1. 切換到 deploy/change_to_vm 分支
git checkout deploy/change_to_vm

# 2. 複製並編輯環境變數
cp .env.vm.example .env.vm
# 編輯 .env.vm，填入實際的密碼與 AWS 金鑰
# 確保包含: DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# 3. 產生自我簽署 SSL 憑證
docker run --rm \
  -v ${PWD}/app/src/ssl:/ssl \
  alpine/openssl \
  req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout /ssl/privkey.pem \
  -out /ssl/fullchain.pem \
  -subj "/CN=localhost"

# 4. 啟動所有服務
docker-compose -f docker-compose-vm.yaml up -d --build

# 5. 確認所有容器正常運行
docker-compose -f docker-compose-vm.yaml ps

# 6. 驗證服務
# 健康檢查:     https://localhost/health
# Django Admin: https://localhost/admin/
# API 文件:     https://localhost/api/schema/swagger-ui/
```

> 💡 瀏覽器存取 `https://localhost` 時會因自我簽署憑證顯示安全警告，
> 點擊「進階」→「繼續前往 localhost（不安全）」即可正常使用。

---

## 服務一覽

使用 `docker-compose-vm.yaml` 啟動的服務：

| 服務 | 說明 | 對外 Port |
|------|------|-----------|
| **nginx** | 反向代理，處理 SSL 終止 | `80`, `443` |
| **backend** | Django + Gunicorn (via Supervisord) | 僅 expose 8000 給 nginx |
| **db** | PostgreSQL 16.2 | 無（僅內部通訊） |
| **rabbitmq** | 訊息佇列 | 無（僅內部通訊） |
| **celery** | 一般任務 Worker | 無 |
| **celery-crawler** | 爬蟲專用 Worker | 無 |
| **celery-beat** | 定時排程 | 無 |
| **selenium** | 瀏覽器自動化（爬蟲用） | `4444` |

# Performance Benchmarks

## 概述

此文件記錄 ComicChase 後端 API 的效能測試結果，作為系統效能的基準參考。

## API 效能測試

### 測試環境

**測試日期:** 2025-12-05

**系統配置:**
- **後端框架:** Django 5.2.8
- **WSGI 伺服器:** Gunicorn 23.0.0
  - Workers: 17 (計算方式: `cpu_count * 2 + 1`)
  - Worker class: sync
  - Timeout: 30s
- **反向代理:** Nginx 1.25.5
  - HTTP/2 enabled
  - SSL termination
- **資料庫:** PostgreSQL 16.2
- **容器化:** Docker Compose

### 測試方法

使用 `wrk` 壓力測試工具進行負載測試：

```bash
wrk -t4 -c100 -d30s https://comicchase.com.tw/api/series/
```

**測試參數:**
- 執行緒數: 4
- 並發連線數: 100
- 測試時長: 30 秒
- 測試端點: `/api/series/` (系列列表 API)

### 測試結果

```
Running 30s test @ https://comicchase.com.tw/api/series/
  4 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   295.74ms   38.93ms 801.74ms   82.95%
    Req/Sec    84.61     28.05   181.00     73.36%
  10084 requests in 30.10s, 3.67MB read
Requests/sec:    335.05
Transfer/sec:    124.99KB
```

**關鍵指標:**
- **每秒請求數 (RPS):** 335.05
- **平均延遲:** 295.74ms
- **標準差:** 38.93ms
- **最大延遲:** 801.74ms
- **總請求數:** 10,084 (30 秒)
- **傳輸速率:** 124.99KB/sec
- **錯誤率:** 0% (無錯誤)

### 結果分析

**優點:**
- ✅ 在 100 個並發連線下穩定運行，無錯誤
- ✅ 延遲分布集中 (82.95% 在平均值附近)
- ✅ 對於包含資料庫查詢的 Django API，335 RPS 表現合理

**可優化項目:**
- 平均延遲 ~300ms 對於 API 來說偏高
- 最大延遲 ~800ms 存在異常值

### 效能優化建議 (Claude Code)

#### 短期優化
1. **資料庫查詢優化**
   - 使用 `select_related()` 和 `prefetch_related()` 減少 N+1 查詢
   - 新增適當的資料庫索引
   - 啟用查詢日誌分析慢查詢

2. **快取策略**
   - 實作 Django 快取框架
   - 對經常存取且變動較少的資料加入快取
   - 考慮使用 Redis 作為快取後端

3. **分頁優化**
   - 確保 API 回應有合理的分頁大小
   - 使用游標分頁 (Cursor Pagination) 改善大數據集效能

#### 長期優化
1. **引入 CDN**
   - 靜態資源透過 CDN 提供
   - 減輕後端伺服器負擔

2. **資料庫讀寫分離**
   - 配置主從複製
   - 讀取請求導向從資料庫

3. **非同步處理**
   - 將耗時操作改為非同步任務 (Celery)
   - 使用訊息佇列處理背景工作

4. **監控與告警**
   - 部署 APM 工具 (如 New Relic、Datadog)
   - 設定效能告警閾值

## 後續測試計畫

- [ ] 實作優化後重新測試並記錄改善幅度
- [ ] 測試其他關鍵 API 端點
- [ ] 進行長時間穩定性測試 (如 1 小時以上)
- [ ] 測試不同並發等級 (50, 200, 500 connections)
- [ ] 壓力測試找出系統瓶頸

## 參考資料

- [Django Performance Optimization](https://docs.djangoproject.com/en/5.2/topics/performance/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)
- [wrk Benchmarking Tool](https://github.com/wg/wrk)

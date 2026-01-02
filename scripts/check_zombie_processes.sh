#!/bin/bash
# 殭屍程序檢查腳本
# 用途：檢查 Celery Worker 執行爬蟲後是否有 Python 或 Chrome 殭屍程序殘留

set -uo pipefail

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查容器是否運行
check_container_running() {
    local container_name=$1
    if ! docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        echo -e "${RED}✗ 容器 ${container_name} 未運行${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ 容器 ${container_name} 正在運行${NC}"
    return 0
}

# Extract all checks into a function
run_checks() {
    echo "========================================"
    echo " 🔍 殭屍程序檢查工具"
    echo " 執行時間: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo ""

    # 檢查基本容器狀態
    echo "1️⃣  檢查容器狀態"
    echo "----------------------------------------"
    check_container_running "comicchase-local-celery-crawler-1"
    CRAWLER_RUNNING=$?
    check_container_running "comicchase-local-selenium-1"
    SELENIUM_RUNNING=$?
    echo ""

    if [ $CRAWLER_RUNNING -ne 0 ] || [ $SELENIUM_RUNNING -ne 0 ]; then
        echo -e "${RED}請先啟動所需容器: docker compose up -d${NC}"
        exit 1
    fi

    # 檢查 Celery Worker 容器中的程序
    # 定義容器名稱變數
    CRAWLER_CONTAINER="comicchase-local-celery-crawler-1"
    SELENIUM_CONTAINER="comicchase-local-selenium-1"

    echo "2️⃣  Celery Crawler 容器程序分析"
    echo "----------------------------------------"

    # Python 程序數量
    PYTHON_COUNT=$(docker exec $CRAWLER_CONTAINER ps aux 2>/dev/null | grep python | grep -v grep | wc -l)
    echo "Python 程序數量: ${PYTHON_COUNT}"

    # Chrome 程序數量（理論上應該是 0，因為 Chrome 在 Selenium 容器中）
    CHROME_COUNT=$(docker exec $CRAWLER_CONTAINER ps aux 2>/dev/null | grep chrome | grep -v grep | wc -l)
    echo "Chrome 程序數量: ${CHROME_COUNT}"

    if [ $CHROME_COUNT -gt 0 ]; then
        echo -e "${YELLOW}⚠️  警告: Crawler 容器中不應該有 Chrome 程序${NC}"
    fi

    # 檢查殭屍程序 (Z state)
    echo ""
    echo "檢查殭屍程序 (Z 狀態):"
    ZOMBIE_OUTPUT=$(docker exec $CRAWLER_CONTAINER ps -eo pid,stat,comm 2>/dev/null | awk 'NR>1 && $2 ~ /Z/' || true)
    if [ -z "$ZOMBIE_OUTPUT" ]; then
        echo -e "${GREEN}✓ 無殭屍程序${NC}"
    else
        echo -e "${RED}✗ 發現殭屍程序:${NC}"
        echo "$ZOMBIE_OUTPUT"
    fi
    echo ""

    # 檢查 Selenium 容器中的 Chrome 程序
    echo "3️⃣  Selenium 容器 Chrome 程序分析"
    echo "----------------------------------------"
    SELENIUM_CHROME_COUNT=$(docker exec $SELENIUM_CONTAINER ps aux 2>/dev/null | grep chrome | grep -v grep | wc -l)
    echo "Chrome 程序總數: ${SELENIUM_CHROME_COUNT}"

    # 正常情況下應該有基礎的 chrome 程序（1-2個）
    # 如果數量過多，可能有殘留
    if [ $SELENIUM_CHROME_COUNT -gt 10 ]; then
        echo -e "${YELLOW}⚠️  警告: Chrome 程序數量異常 (>10)，可能有殘留${NC}"
    elif [ $SELENIUM_CHROME_COUNT -gt 5 ]; then
        echo -e "${YELLOW}⚠️  注意: Chrome 程序數量較多 (${SELENIUM_CHROME_COUNT})${NC}"
    else
        echo -e "${GREEN}✓ Chrome 程序數量正常${NC}"
    fi

    # 顯示詳細的 Chrome 程序（僅顯示主要的）
    echo ""
    echo "Chrome 主要程序:"
    docker exec $SELENIUM_CONTAINER ps aux 2>/dev/null | grep "[c]hrome --type" | head -5
    echo ""

    # 檢查容器資源使用
    echo "4️⃣  容器資源使用情況"
    echo "----------------------------------------"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" \
        $CRAWLER_CONTAINER $SELENIUM_CONTAINER
    echo ""

    # 提供建議
    echo "5️⃣  建議與說明"
    echo "----------------------------------------"
    echo "📋 正常基線值:"
    echo "   - Celery Crawler Python 程序: 3-5 個 (主程序 + worker 子程序)"
    echo "   - Celery Crawler Chrome 程序: 0 個"
    echo "   - Selenium Chrome 程序: 1-3 個 (待命狀態)"
    echo "   - 殭屍程序: 0 個"
    echo ""
    echo "🔧 如何測試:"
    echo "   1. 記錄當前狀態（執行此腳本）"
    echo "   2. 執行一個測試任務"
    echo "   3. 等待任務完成（檢查 logs）"
    echo "   4. 再次執行此腳本比對"
    echo ""
    echo "🧹 如何清理殘留程序:"
    echo "   docker restart $CRAWLER_CONTAINER"
    echo "   docker restart $SELENIUM_CONTAINER"
    echo ""

    echo "========================================"
    echo " ✅ 檢查完成"
    echo "========================================"
}

# Run checks once
run_checks

# 進階: 如果提供 --watch 參數，則持續監控
if [ "${1:-}" == "--watch" ]; then
    INTERVAL=${2:-30}
    # Validate interval is numeric
    if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]]; then
        echo -e "${RED}錯誤: 間隔必須是數字${NC}"
        exit 1
    fi
    echo "🔄 進入監控模式 (每 ${INTERVAL} 秒更新一次，按 Ctrl+C 退出)"
    echo ""

    while true; do
        sleep $INTERVAL
        clear
        run_checks
    done
fi

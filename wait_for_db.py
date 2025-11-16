import socket
import time
import os
import subprocess

# 從環境變數讀取設定
host = os.environ.get('DB_HOST', 'db')
port = int(os.environ.get('DB_PORT', 5432))
timeout = 1  # 每次連線嘗試的超時時間 (秒)
max_retries = 30 # 最多嘗試 30 次

print(f"Waiting for database at {host}:{port}...")

retries = 0
while retries < max_retries:
    try:
        # 建立一個 socket 連線
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
        
        print(f"Database at {host}:{port} is ready!")
        
        # 自動執行資料庫遷移 
        print("Running database migrations...")
        try:
            subprocess.run(
                ["python", "/app/manage.py", "migrate"], 
                check=True,
                capture_output=True, # 捕獲標準輸出/錯誤
                text=True
            )
            print("Migrations applied successfully.")
        
        except subprocess.CalledProcessError as e:
            # 失敗印出錯誤訊息並停止
            print("--- MIGRATION FAILED ---")
            print(e.stdout)
            print(e.stderr)
            print("--------------------------")
            print("Exiting due to migration failure.")
            exit(1) 


        
        print("Starting Django server...")
        args = ["python", "/app/manage.py", "runserver", "0.0.0.0:8000"]
        os.execvp(args[0], args)
        
    except (socket.timeout, ConnectionRefusedError):
        retries += 1
        print(f"Database not ready yet (attempt {retries}/{max_retries})... retrying in 1 second.")
        time.sleep(1)

print(f"Failed to connect to database after {max_retries} attempts. Exiting.")
exit(1)
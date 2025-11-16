import os
import sys


def main():
    """運行管理任務 Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "無法匯入 Django。"
            "請確定它已安裝並且已新增至 PYTHONPATH 環境變數中"
            "是否已啟動虛擬環境？ "
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable?"
            "Did you forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

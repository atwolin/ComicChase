
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./src .
RUN chmod +x /code/wait-for-it.sh

# 修復 Windows 行尾符問題（CRLF -> LF）並設置執行權限
RUN if [ -f /code/wait-for-it.sh ]; then \
    sed -i 's/\r$//' /code/wait-for-it.sh && \
    chmod +x /code/wait-for-it.sh; \
    fi

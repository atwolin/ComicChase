
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

RUN pip install --upgrade pip
COPY ./app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app/src .

# Fix Windows line endings issue for wait-for-it.sh
RUN sed -i 's/\r$//' /code/wait-for-it.sh && \
    chmod +x /code/wait-for-it.sh


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

RUN pip install --upgrade pip
COPY ./app/requirements.txt .
RUN pip install -r requirements.txt

COPY ./app/src .

# Copy wait-for-it.sh to a location that won't be overridden by bind mounts
RUN mkdir -p /scripts
COPY ./app/src/wait-for-it.sh /scripts/wait-for-it.sh

# Fix Windows line endings issue for wait-for-it.sh and ensure it's executable
RUN sed -i 's/\r$//' /scripts/wait-for-it.sh && \
    chmod +x /scripts/wait-for-it.sh

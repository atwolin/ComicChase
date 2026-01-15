
FROM python:3.12-slim

ARG USER_ID=1000
ARG GID=1000

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code/app

# Create non-root user
RUN groupadd -g $GID docker-users && \
    useradd -m --no-log-init -s /bin/bash -u $USER_ID -g $GID docker && \
    echo "docker:docker" | chpasswd && \
    adduser docker sudo

# Install system dependencies for pygraphviz
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     graphviz \
#     graphviz-dev \
#     pkg-config \
#     && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY ./app/requirements.txt ./
RUN pip install -r requirements.txt

COPY ./app/src ./

RUN chmod +x entrypoint.sh wait-for-it.sh

# Set ownership and permissions
RUN chown -R docker:docker-users /code/app

USER docker

ENTRYPOINT [ "/code/app/entrypoint.sh" ]

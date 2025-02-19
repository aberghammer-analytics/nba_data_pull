FROM python:3.11-bookworm

ARG UV_VERSION=0.2.24
ARG UV_URL=github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-installer.sh 

RUN apt-get update && \
    apt-get install -y build-essential curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -LsSf https://${UV_URL} | sh
#!/bin/bash

# Генерация .env файла из переменных окружения для MergeBlocker
# Используется в CI/CD pipeline

set -e

echo "🔧 Генерируем .env файл из переменных окружения..."

cat > .env << EOF
# GitHub App Configuration
GITHUB_APP_ID=${GITHUB_APP_ID}
GITHUB_PRIVATE_KEY_PATH=./private-key.pem
GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}

# LLM Configuration (OpenRouter-compatible API)
LLM_API_KEY=${LLM_API_KEY}
LLM_API_BASE_URL=${LLM_API_BASE_URL:-https://openrouter.ai/api/v1}
LLM_MODEL=${LLM_MODEL:-eliza-Claude-Sonnet-4-5}
LLM_TEMPERATURE=${LLM_TEMPERATURE:-1.0}
LLM_MAX_TOKENS=${LLM_MAX_TOKENS:-64000}
LLM_TIMEOUT=${LLM_TIMEOUT:-180}

# Server Configuration
PORT=${PORT:-8002}
HOST=${HOST:-0.0.0.0}
DEBUG=${DEBUG:-False}
SKIP_DRAFT_PRS=${SKIP_DRAFT_PRS:-True}
EOF

echo "✅ Файл .env создан"

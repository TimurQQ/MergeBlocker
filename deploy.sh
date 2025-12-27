#!/bin/bash

# Скрипт для деплоя MergeBlocker в продакшене
# Использует готовый образ из GitHub Container Registry

set -e

echo "🚀 Начинаем деплой MergeBlocker..."

# Генерируем .env файл если есть переменные окружения
if [ -n "$GITHUB_APP_ID" ]; then
    echo "🔧 Генерируем .env файл из переменных окружения..."
    ./generate-env.sh
elif [ ! -f .env ]; then
    echo "❌ Файл .env не найден и переменные окружения не установлены!"
    echo "Создайте .env файл или установите переменные окружения."
    echo "Пример содержимого:"
    echo "GITHUB_APP_ID=2469635"
    echo "GITHUB_WEBHOOK_SECRET=your_secret"
    echo "LLM_API_KEY=your_api_key"
    echo "LLM_API_BASE_URL=https://your-api-url.com/v1"
    exit 1
else
    echo "✅ Используем существующий .env файл"
fi

# Проверяем наличие private key
if [ ! -f private-key.pem ]; then
    echo "❌ Файл private-key.pem не найден!"
    echo "GitHub App private key должен быть размещен в: ./private-key.pem"
    exit 1
fi
echo "✅ Private key найден"

# Останавливаем текущие контейнеры
echo "🛑 Останавливаем текущие контейнеры..."
docker compose -f docker-compose.prod.yaml down || true

# Запускаем новые контейнеры (pull + recreate в одной команде)
echo "🚀 Запускаем контейнеры с проверкой обновлений..."
docker compose -f docker-compose.prod.yaml up -d --force-recreate --pull always

# Ждем запуска сервиса
echo "⏳ Ждем запуска сервиса..."
sleep 15

# Проверяем здоровье сервиса
echo "🔍 Проверяем состояние сервиса..."
if curl -f http://localhost:8002/ > /dev/null 2>&1; then
    echo "✅ MergeBlocker успешно запущен!"
    echo "📊 Статус контейнеров:"
    docker compose -f docker-compose.prod.yaml ps
else
    echo "❌ Ошибка запуска MergeBlocker"
    echo "📋 Логи сервиса:"
    docker compose -f docker-compose.prod.yaml logs mergeblocker
    exit 1
fi

# Очищаем неиспользуемые образы
echo "🧹 Очищаем неиспользуемые образы..."
docker system prune -f

echo "✅ Деплой MergeBlocker завершен успешно!"
echo "🌐 API доступен по адресу: http://localhost:8002"
echo ""
echo "💡 Полезные команды:"
echo "   docker compose -f docker-compose.prod.yaml logs -f    # Просмотр логов"
echo "   docker compose -f docker-compose.prod.yaml restart    # Перезапуск"
echo "   docker compose -f docker-compose.prod.yaml down       # Остановка"

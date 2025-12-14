# 🚀 Deployment Guide для MergeBlocker

Руководство по настройке автоматического CI/CD деплоя MergeBlocker.

## 📋 Архитектура деплоя

```
GitHub Push (master)
    ↓
GitHub Actions
    ├─ Build Docker Image
    ├─ Push to GHCR (GitHub Container Registry)
    └─ SSH Deploy to Server
        ├─ Pull latest code
        ├─ Pull Docker image
        ├─ Generate .env
        └─ Run deploy.sh
```

## 🔧 Настройка GitHub Secrets

Перейдите в Settings → Secrets and variables → Actions и добавьте следующие secrets:

### Обязательные секреты:

#### 1. **Server SSH Access**
```
MERGEBLOCKER_SERVER_HOST=your-server-ip
MERGEBLOCKER_SERVER_USER=deploy
MERGEBLOCKER_SERVER_SSH_KEY=<ваш приватный SSH ключ>
MERGEBLOCKER_SERVER_PORT=22
MERGEBLOCKER_SERVER_PROJECT_PATH=/opt/mergeblocker
```

**Примечание:** Используется тот же пользователь `deploy` что и в ML-API проекте.

#### 2. **GitHub App Configuration**
```
APP_ID=2469635
WEBHOOK_SECRET=<ваш webhook secret>
PRIVATE_KEY_BASE64=<base64 encoded private key>
```

**Примечание:** GitHub не позволяет создавать секреты с префиксом `GITHUB_`, поэтому используем короткие имена.

**Как получить PRIVATE_KEY_BASE64:**
```bash
base64 -i private-key.pem | tr -d '\n'
```

#### 3. **LLM API (OpenRouter-compatible)**
```
LLM_API_KEY=your_api_key_here
LLM_API_BASE_URL=https://your-api-url.com/v1
LLM_MODEL=eliza-Internal-DeepSeek-V3-1-Terminus
```

**Примечание:** Используется та же LLM конфигурация что и в ML-API проекте.

#### 4. **Server Configuration (опционально)**
```
PORT=8002
HOST=0.0.0.0
DEBUG=False
```

**Примечание:** Порт 8002 используется чтобы не конфликтовать с ML-API (порт 8000) и другими сервисами.

## 🖥️ Подготовка сервера

### 1. Создайте пользователя для деплоя (если еще не создан)

```bash
# Создайте пользователя deploy (тот же что и для ML-API)
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy
```

### 2. Установите Docker и Docker Compose

```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl enable docker
sudo systemctl start docker

# Установите Docker Compose
sudo apt install docker-compose-plugin -y
```

### 3. Подготовьте директорию проекта

```bash
# Создайте директорию под пользователем deploy
sudo mkdir -p /opt/mergeblocker
sudo chown deploy:deploy /opt/mergeblocker

# Клонируйте репозиторий (под пользователем deploy)
su - deploy
git clone git@github.com:TimurQQ/MergeBlocker.git /opt/mergeblocker
cd /opt/mergeblocker
```

### 4. Настройте SSH ключ для GitHub Actions

Локально (на вашей машине):
```bash
# Создайте SSH ключ для деплоя
ssh-keygen -t rsa -b 4096 -C "mergeblocker-deploy" -f ~/.ssh/mergeblocker_deploy_key

# Скопируйте публичный ключ на сервер
ssh-copy-id -i ~/.ssh/mergeblocker_deploy_key.pub deploy@your-server

# Скопируйте приватный ключ для GitHub Secrets
cat ~/.ssh/mergeblocker_deploy_key
```

Добавьте содержимое приватного ключа в GitHub Secrets как `MERGEBLOCKER_SERVER_SSH_KEY`.

## 🔐 Настройка GHCR (GitHub Container Registry)

### 1. Сделайте пакет публичным (опционально)

1. Перейдите в https://github.com/users/TimurQQ/packages/container/mergeblocker/settings
2. В разделе "Danger Zone" → "Change package visibility" → "Public"

### 2. Или настройте доступ для сервера

На сервере:
```bash
# Создайте Personal Access Token с правами read:packages
# https://github.com/settings/tokens

# Логин в GHCR
echo "YOUR_TOKEN" | docker login ghcr.io -u TimurQQ --password-stdin
```

## 🚀 Процесс деплоя

### Автоматический деплой

При push в ветку `master`:

1. **Build** - собирается Docker образ
2. **Push** - образ пушится в GHCR
3. **Deploy** - через SSH:
   - Обновляется код (`git pull`)
   - Скачивается новый образ
   - Генерируется `.env`
   - Создается `private-key.pem` из секрета
   - Запускается `deploy.sh`

### Ручной деплой

На сервере:

```bash
cd /path/to/MergeBlocker

# Обновите код
git pull origin master

# Установите переменные окружения
export GITHUB_APP_ID="2469635"
export GITHUB_WEBHOOK_SECRET="your_secret"
export LLM_API_KEY="your_api_key"
export LLM_API_BASE_URL="https://your-api-url.com/v1"

# Создайте private key (если нужно)
echo "$PRIVATE_KEY_BASE64" | base64 -d > private-key.pem
chmod 600 private-key.pem

# Запустите деплой
./deploy.sh
```

## 📊 Мониторинг

### Просмотр логов

```bash
# Логи в реальном времени
docker compose -f docker-compose.prod.yaml logs -f

# Последние 100 строк
docker compose -f docker-compose.prod.yaml logs --tail=100

# Логи конкретного контейнера
docker compose -f docker-compose.prod.yaml logs mergeblocker
```

### Проверка статуса

```bash
# Статус контейнеров
docker compose -f docker-compose.prod.yaml ps

# Healthcheck
curl http://localhost:8002/

# Детальная информация
docker inspect mergeblocker-mergeblocker-1
```

### Перезапуск

```bash
# Перезапуск сервиса
docker compose -f docker-compose.prod.yaml restart

# Полный рестарт (с пересозданием контейнеров)
docker compose -f docker-compose.prod.yaml down
docker compose -f docker-compose.prod.yaml up -d
```

## 🔄 Rollback

Если что-то пошло не так:

```bash
# Откатитесь к предыдущему коммиту
git log --oneline  # Найдите нужный коммит
git reset --hard <commit-hash>

# Или используйте конкретную версию образа
docker compose -f docker-compose.prod.yaml down
docker pull ghcr.io/timurqq/mergeblocker:<commit-sha>

# Отредактируйте docker-compose.prod.yaml, замените :latest на :<commit-sha>
docker compose -f docker-compose.prod.yaml up -d
```

## 🐛 Troubleshooting

### Проблема: Деплой не запускается

**Проверьте:**
1. GitHub Actions логи: https://github.com/TimurQQ/MergeBlocker/actions
2. Все ли secrets настроены правильно
3. SSH доступ к серверу работает

### Проблема: Docker образ не скачивается

**Решение:**
```bash
# Проверьте логин в GHCR
docker login ghcr.io

# Попробуйте скачать вручную
docker pull ghcr.io/timurqq/mergeblocker:latest
```

### Проблема: Контейнер не запускается

**Проверьте:**
```bash
# Логи контейнера
docker compose -f docker-compose.prod.yaml logs

# Проверьте .env файл
cat .env

# Проверьте private-key.pem
ls -la private-key.pem
```

### Проблема: Webhook не работает

**Проверьте:**
1. Порт 8002 открыт на сервере
2. Nginx/reverse proxy настроен правильно
3. GitHub Webhook URL указывает на сервер
4. Webhook secret совпадает

## 🔒 Безопасность

### Рекомендации:

1. **Используйте firewall**
   ```bash
   sudo ufw allow 22/tcp  # SSH
   sudo ufw allow 80/tcp  # HTTP
   sudo ufw allow 443/tcp # HTTPS
   sudo ufw enable
   ```

2. **Настройте Nginx как reverse proxy**
   ```nginx
   server {
       listen 80;
       server_name mergeblocker.yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8002;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Используйте SSL/TLS (Let's Encrypt)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d mergeblocker.yourdomain.com
   ```

4. **Регулярно обновляйте систему**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## 📈 Масштабирование

### Несколько воркеров

Отредактируйте `Dockerfile`:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:8002", "--workers", "8", ...]
```

### Load Balancer

Используйте Nginx для балансировки между несколькими инстансами:
```nginx
upstream mergeblocker {
    server localhost:8002;
    server localhost:8003;
    server localhost:8004;
}
```

## 📚 Дополнительные ресурсы

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [GHCR Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

---

**Вопросы?** Создайте issue в репозитории!


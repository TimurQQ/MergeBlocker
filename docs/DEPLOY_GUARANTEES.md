# Гарантии деплоя

## Изменения в коде → гарантированное обновление ✅

### Как это работает:

1. **CI собирает образ:**
   ```dockerfile
   COPY app.py .        # ← Если файл изменился → слой пересоберётся
   COPY src/ ./src/     # ← Docker layer cache инвалидируется
   ```

2. **Создаются два тега:**
   ```yaml
   tags: |
     ghcr.io/timurqq/mergeblocker:latest           # Всегда перезаписывается
     ghcr.io/timurqq/mergeblocker:${{ github.sha }} # Уникальный тег commit
   ```

3. **Деплой на сервере:**
   ```bash
   docker compose pull              # Скачивает новый образ
   docker compose up -d \
     --force-recreate \             # Пересоздаёт контейнер
     --pull always                  # Проверяет обновления образа
   ```

**Гарантия:** ✅ Новый код **всегда** задеплоится, потому что:
- Новый SHA образа → Docker распознаёт изменение
- `--force-recreate` → контейнер пересоздаётся принудительно
- `--pull always` → проверяет registry на обновления

## Изменения в secrets → гарантированное обновление ✅

### Как это работает:

1. **CI обновляет secrets на сервере:**
   ```bash
   # В deploy.yaml перед вызовом deploy.sh:
   export GITHUB_APP_ID="${{ secrets.APP_ID }}"
   export LLM_API_KEY="${{ secrets.LLM_API_KEY }}"
   # ... и другие

   # Создаём private key
   echo "${{ secrets.PRIVATE_KEY_BASE64 }}" | base64 -d > private-key.pem

   # Генерируем новый .env
   ./generate-env.sh
   ```

2. **Docker образ может быть тот же:**
   ```
   Образ SHA: тот же (код не изменился, кэш)
   .env файл: новые значения! ✅
   private-key.pem: новое содержимое! ✅
   ```

3. **Деплой гарантирует обновление:**
   ```bash
   docker compose down              # Удаляет контейнер
   docker compose pull              # Проверяет образ
   docker compose up -d \
     --force-recreate \             # Пересоздаёт контейнер ВСЕГДА
     --pull always                  # Проверяет обновления
   ```

**Гарантия:** ✅ Новые secrets **всегда** применятся, потому что:
- `down` → удаляет старый контейнер
- `--force-recreate` → создаёт новый контейнер (читает .env заново)
- Secrets передаются в runtime, не в образ

## Изменения в обоих (код + secrets) ✅

```
CI:
├── Код изменился → новый Docker образ SHA
├── Secrets обновились → новый .env на сервере
└── Пушит образ с тегом :latest и :${{ github.sha }}

Сервер:
├── Создаёт новый .env из secrets ✅
├── Скачивает новый образ ✅
├── Удаляет старый контейнер ✅
└── Создаёт новый контейнер с новым кодом и secrets ✅
```

## Дополнительные гарантии

### 1. Healthcheck после деплоя

```bash
# deploy.sh проверяет работоспособность:
sleep 15
if curl -f http://localhost:8002/ > /dev/null 2>&1; then
    echo "✅ MergeBlocker успешно запущен!"
else
    echo "❌ Ошибка запуска"
    docker compose logs mergeblocker
    exit 1
fi
```

**Гарантия:** Деплой провалится, если сервис не отвечает.

### 2. Атомарность деплоя

```bash
set -e  # Прервать выполнение при любой ошибке
```

**Гарантия:** Если любая команда в deploy.sh провалится, деплой остановится.

### 3. Логи при ошибках

```bash
if [ deploy failed ]; then
    docker compose logs mergeblocker  # Показывает логи
    exit 1
fi
```

**Гарантия:** При ошибке вы получите полные логи.

### 4. Очистка старых образов

```bash
docker system prune -f  # Удаляет неиспользуемые образы
```

**Гарантия:** Не захламляется диск старыми образами.

## Граничные случаи

### Случай 1: Только secrets изменились, код нет

```
Образ: тот же SHA (закэширован в CI)
.env: новые значения

Результат:
├── docker compose pull → "Image is up to date"
├── docker compose down → удалил контейнер ✅
└── docker compose up -d --force-recreate → создал новый ✅
    └── Новый контейнер читает обновлённый .env! ✅
```

### Случай 2: Только код изменился, secrets нет

```
Образ: новый SHA
.env: те же значения

Результат:
├── docker compose pull → скачал новый образ ✅
├── docker compose down → удалил контейнер ✅
└── docker compose up -d --force-recreate → создал новый ✅
    └── Новый контейнер с новым кодом! ✅
```

### Случай 3: Ничего не изменилось (redeploy)

```
Образ: тот же SHA
.env: те же значения

Результат:
├── docker compose pull → "Image is up to date"
├── docker compose down → удалил контейнер ✅
└── docker compose up -d --force-recreate → создал новый ✅
    └── Контейнер пересоздан (полезно для сброса состояния)
```

## Флаги для гарантий

### `--force-recreate`

```bash
docker compose up -d --force-recreate
```

**Что делает:**
- Пересоздаёт контейнеры, даже если конфигурация не изменилась
- Игнорирует кэш запущенных контейнеров
- Гарантирует, что secrets из .env будут перечитаны

### `--pull always`

```bash
docker compose up -d --pull always
```

**Что делает:**
- Всегда проверяет registry на обновления образа
- Скачивает образ, даже если локально есть с тем же тегом
- Гарантирует актуальность образа

## Команды для ручной проверки

### На сервере проверить текущую версию:

```bash
# Проверить SHA образа
docker inspect ghcr.io/timurqq/mergeblocker:latest | grep Id

# Проверить переменные окружения контейнера
docker inspect mergeblocker-mergeblocker-1 | grep -A 20 Env

# Проверить дату создания контейнера
docker inspect mergeblocker-mergeblocker-1 | grep Created
```

### Проверить, что .env обновился:

```bash
# На сервере
cat .env | grep LLM_API_KEY
```

### Принудительный деплой:

```bash
# На сервере
./deploy.sh  # Всегда пересоздаёт контейнер благодаря --force-recreate
```

## Итого: Двойная гарантия

1. **Код изменился:**
   - ✅ Новый Docker образ SHA
   - ✅ `--pull always` скачает новый образ
   - ✅ `--force-recreate` создаст новый контейнер

2. **Secrets изменились:**
   - ✅ Новый .env файл на сервере
   - ✅ `down` удалит старый контейнер
   - ✅ `--force-recreate` создаст новый (с новым .env)

**Вывод:** Изменения в коде и secrets **гарантированно** применятся в продакшене! 🎯

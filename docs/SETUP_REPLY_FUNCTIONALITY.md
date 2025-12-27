# Настройка Reply Functionality для MergeBlocker

## 🎯 Что это дает

После настройки бот сможет отвечать на вопросы в комментариях к коду, создавая полноценный диалог:

1. Бот оставляет inline комментарий к коду в Files Changed
2. Пользователь отвечает на комментарий с вопросом
3. Бот автоматически отвечает, используя контекст PR и кода

## ⚙️ Настройка GitHub App

### 1. Перейдите в настройки вашего GitHub App

URL: https://github.com/settings/apps/mergeblocker

### 2. В разделе **Subscribe to events** добавьте:

- ✅ **Pull request** (уже должно быть)
- ✅ **Issue comment** (уже должно быть)
- ✅ **Pull request review comment** ← **ДОБАВЬТЕ ЭТО!**

### 3. Сохраните изменения

Нажмите **Save changes** внизу страницы.

## 🔍 Как это работает

### Типы комментариев в GitHub

GitHub различает два типа комментариев в PR:

1. **Issue comments** (`issue_comment` event):
   - Комментарии в основной conversation thread PR
   - Используются для команд типа `@MergeBlocker review`

2. **Review comments** (`pull_request_review_comment` event):
   - Inline комментарии к конкретным строкам кода в Files Changed
   - Создаются через GitHub Reviews API
   - **Именно к ним можно делать reply!**

### Почему нужно отдельное событие

Когда пользователь отвечает на inline комментарий бота в Files Changed, GitHub отправляет webhook с типом `pull_request_review_comment` и полем `in_reply_to_id`.

Без подписки на это событие бот не получит уведомление о reply.

## 📝 Что изменилось в коде

1. **`src/handlers/webhook_handler.py`**:
   - `is_comment_event()` теперь обрабатывает оба типа событий
   - `extract_pr_info_from_comment()` корректно извлекает данные из обоих форматов

2. **`app.py`**:
   - `handle_comment_reply()` корректно определяет PR number для обоих типов событий

## ✅ Проверка

После настройки:

1. Создайте тестовый PR
2. Запустите review: `@MergeBlocker review`
3. Дождитесь inline комментария бота
4. Нажмите "Reply" на комментарии бота
5. Напишите вопрос
6. Бот должен автоматически ответить!

## 🐛 Troubleshooting

### Бот не отвечает на reply

1. Проверьте что **Pull request review comment** event добавлен
2. Проверьте логи webhook в GitHub App (Settings → Apps → Advanced → Recent Deliveries)
3. Должны быть события типа `pull_request_review_comment` с action `created`

### Ошибка "Parent comment not found"

- Это может произойти если parent комментарий был удален
- Или если reply был сделан не на комментарий бота

### Reply работает для issue_comment, но не для review_comment

- Убедитесь что вы подписались именно на **Pull request review comment** event
- Перезапустите webhook delivery в Recent Deliveries для проверки

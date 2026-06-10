# Деплой на Render.com (бесплатно)

Render даёт бесплатный веб-сервер с HTTPS — это нужно для Telegram Web App.

> **Важно:** на бесплатном тарифе сервер «засыпает» после 15 минут без запросов. Первый запуск после сна занимает ~30 секунд. Для кухни это обычно нормально.

> **База данных:** SQLite на Render сбрасывается при перезапуске. Для постоянного хранения позже можно подключить [Neon PostgreSQL](https://neon.tech) (тоже бесплатно).

---

## Шаг 0. Исправьте `.env` (локально)

В файле `.env` должны быть **разные** значения:

```env
BOT_TOKEN=123456789:ABCdef...        ← токен от @BotFather (длинная строка с двоеточием)
ADMIN_TELEGRAM_ID=729409944          ← ваш числовой ID от @userinfobot
WEBAPP_URL=https://kitchen-bot.onrender.com   ← URL после деплоя (пока можно оставить localhost)
WEBHOOK_MODE=false                   ← локально false, на Render true
API_PORT=8000
```

**Частая ошибка:** токен бота и Telegram ID перепутаны местами.

Узнать ID: напишите боту `/myid` или [@userinfobot](https://t.me/userinfobot).

---

## Шаг 1. Загрузите код на GitHub

1. Зарегистрируйтесь на [github.com](https://github.com)
2. Создайте новый репозиторий (например `kitchen-bot`)
3. В папке проекта выполните:

```powershell
cd "f:\софт для кухни"
git init
git add .
git commit -m "Kitchen Telegram bot"
git branch -M main
git remote add origin https://github.com/ВАШ_ЛОГИН/kitchen-bot.git
git push -u origin main
```

Файл `.env` в git не попадёт (он в `.gitignore`) — это правильно, секреты не должны быть в репозитории.

---

## Шаг 2. Создайте сервис на Render

1. Зайдите на [render.com](https://render.com) → Sign Up (можно через GitHub)
2. **New +** → **Web Service**
3. Подключите репозиторий `kitchen-bot`
4. Настройки:
   - **Name:** `kitchen-bot`
   - **Region:** Frankfurt (ближе к РФ)
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

5. В разделе **Environment Variables** добавьте:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | токен от BotFather |
| `ADMIN_TELEGRAM_ID` | ваш числовой Telegram ID |
| `WEBAPP_URL` | пока оставьте пустым — заполните после деплоя |
| `WEBHOOK_MODE` | `true` |

6. Нажмите **Create Web Service**

---

## Шаг 3. Укажите URL приложения

После деплоя Render даст URL вида:

```
https://kitchen-bot-xxxx.onrender.com
```

1. Render → ваш сервис → **Environment** → измените `WEBAPP_URL` на этот URL
2. Нажмите **Manual Deploy** → **Deploy latest commit**

При старте бот автоматически зарегистрирует webhook на `https://.../webhook`.

---

## Шаг 4. Настройте бота в BotFather

1. Откройте [@BotFather](https://t.me/BotFather)
2. `/mybots` → выберите бота → **Bot Settings** → **Menu Button** → **Configure menu button**
3. URL: `https://kitchen-bot-xxxx.onrender.com`
4. Текст кнопки: `Открыть кухню`

Опционально — описание:
```
/setdescription
Система управления кухней: смены, ревизия, ТТК
```

---

## Шаг 5. Проверка

1. Откройте бота в Telegram → `/start`
2. Нажмите **Открыть кухню**
3. Вы (админ) должны увидеть вкладку **Роли**
4. Отправьте ссылку на бота коллеге → он откроет приложение → появится в **Роли**

---

## Как работают пользователи и роли

```
Сотрудник                    Админ (вы)
    │                            │
    ├─ Открывает бота            │
    ├─ /start                    │
    ├─ «Открыть кухню»           │
    │                            │
    └─ Автоматически ───────────►├─ Вкладка «Роли»
       регистрируется             ├─ Видит нового пользователя
       как «Повар»                └─ Меняет роль на Шеф / Повар
```

- **Добавлять вручную никого не нужно** — человек появляется в списке после первого входа в приложение
- **Админ** — тот, чей `ADMIN_TELEGRAM_ID` указан в настройках (вы)
- **Повар / Шеф** — назначаете вы во вкладке «Роли»

---

## Локальный запуск (без деплоя)

```powershell
.\venv\Scripts\activate
# WEBHOOK_MODE=false в .env
python run.py
```

Для Web App локально нужен HTTPS — используйте [ngrok](https://ngrok.com):

```powershell
# Терминал 1
python run.py api

# Терминал 2
ngrok http 8000
```

URL из ngrok → `WEBAPP_URL` в `.env` → перезапустите бота.

---

## Проблемы

| Симптом | Решение |
|---------|---------|
| «Ошибка загрузки» в приложении | Проверьте `WEBAPP_URL` — должен совпадать с URL сервера |
| Бот не отвечает | Проверьте `BOT_TOKEN`, `WEBHOOK_MODE=true` на Render |
| Нет вкладки «Роли» | Проверьте `ADMIN_TELEGRAM_ID` — это число, не токен |
| Данные пропали | Бесплатный Render сбрасывает SQLite — подключите Neon DB |

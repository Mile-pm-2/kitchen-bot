# Деплой на Render.com (бесплатно)

Render даёт бесплатный веб-сервер с HTTPS — это нужно для Telegram Web App.

> **Важно:** на бесплатном тарифе сервер «засыпает» после 15 минут без запросов. Первый запуск после сна занимает ~30 секунд. Для кухни это обычно нормально.

> **База данных:** для постоянного хранения используйте [Neon PostgreSQL](https://neon.tech). SQLite на Render может сбрасываться при перезапуске.

---

## Шаг 0. Исправьте `.env` (локально)

В файле `.env` должны быть **разные** значения:

```env
BOT_TOKEN=your_bot_token_here        ← токен от @BotFather (длинная строка с двоеточием)
ADMIN_TELEGRAM_ID=123456789          ← ваш числовой ID от @userinfobot
WEBAPP_URL=https://kitchen-bot-lcrf.onrender.com   
WEBHOOK_MODE=true                   ← локально false, на Render true
API_PORT=8000
DATABASE_URL=postgresql://user:password@host/neondb?sslmode=require
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
   - **Runtime:** **Docker** ← важно! (не Python)
   - **Dockerfile Path:** `./Dockerfile` (по умолчанию)
   - **Plan:** Free

> Почему Docker? На Render сейчас нет выбора версии Python в интерфейсе — ставится 3.14, из‑за чего падает сборка. Dockerfile фиксирует Python 3.11.

5. В разделе **Environment Variables** добавьте:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | токен от BotFather |
| `ADMIN_TELEGRAM_ID` | ваш числовой Telegram ID |
| `WEBAPP_URL` | пока оставьте пустым — заполните после деплоя |
| `WEBHOOK_MODE` | `true` |
| `DATABASE_URL` | строка подключения Neon PostgreSQL |

6. Нажмите **Create Web Service**

### Постоянная база Neon

1. Зайдите на [neon.tech](https://neon.tech) и создайте бесплатный проект.
2. Скопируйте строку подключения вида `postgresql://...`.
3. В Render → ваш сервис → **Environment** добавьте `DATABASE_URL`.
4. Не добавляйте реальную строку подключения в git, `.env.example` или документацию.
5. Если строка подключения уже была отправлена в чат или лог, перевыпустите пароль в Neon и обновите `DATABASE_URL` в Render.

Приложение само преобразует Neon URL в async-формат SQLAlchemy при запуске.

### Уже создали сервис с Runtime = Python?

Вариант А — пересоздать (проще):
1. Удалите старый Web Service
2. Создайте новый с **Runtime: Docker**

Вариант Б — сменить runtime:
1. Render → ваш сервис → **Settings**
2. Прокрутите до **Build & Deploy**
3. Если есть поле **Runtime** — смените на **Docker**
4. **Save Changes** → **Manual Deploy**

Затем залейте код с `Dockerfile`:
```powershell
git add .
git commit -m "Add Dockerfile for Render"
git push
```

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
Система управления кухней: ревизия, ТТК, заказы
```

---

## Шаг 5. Проверка

1. Откройте бота в Telegram → `/start`
2. Нажмите **Открыть кухню**
3. Вы должны увидеть главный экран **ТТК**
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
       как «Повар»                └─ Меняет роль на Су-шеф / Шеф / Повар
```

- **Добавлять вручную никого не нужно** — человек появляется в списке после `/start` или первого входа в приложение
- **Админ** — тот, чей `ADMIN_TELEGRAM_ID` указан в настройках (вы)
- **Повар** видит роли, но не редактирует
- **Су-шеф** может назначать повара и су-шефа
- **Шеф** может назначать повара, су-шефа и шефа

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
| `pydantic-core` / `python3.14` / `maturin failed` | Переключите Runtime на **Docker** (не Python). В репозитории уже есть `Dockerfile` с Python 3.11 |

# Retro-Streamer 🎮

**Backend-сервис для асинхронного рендеринга ретро-игр с REST API, WebSocket-обновлениями и системой рейтингов.**

Retro-Streamer — pet-проект на FastAPI, демонстрирующий разработку backend-сервиса с авторизацией, фоновой обработкой задач, хранением результатов и интерактивной API-документацией.

## Возможности

- 🔐 **Авторизация** — JWT-токены и безопасное хеширование паролей.
- 🎮 **Игровой рендеринг** — работа с Snake, 2048, Labyrinth и Sokoban.
- ⚙️ **Фоновые задачи** — асинхронная обработка через Celery и Redis.
- 🔄 **WebSocket** — передача обновлений о выполнении задач в реальном времени.
- 🗄️ **Хранение данных** — PostgreSQL, SQLAlchemy и миграции Alembic.
- 📦 **Хранение результатов** — интеграция с S3-совместимым хранилищем MinIO.
- 🏆 **Leaderboard** — API для получения игровых рейтингов.
- 🐳 **Docker Compose** — контейнеризация и совместный запуск сервисов.
- 🧪 **Тестирование** — pytest.

## Технологический стек

| Категория | Технологии |
|---|---|
| API | Python, FastAPI, Pydantic |
| База данных | PostgreSQL, SQLAlchemy, Alembic |
| Очередь задач | Celery, Redis |
| Авторизация | JWT, Argon2 |
| Хранение файлов | MinIO, S3 API |
| Реальное время | WebSocket |
| Инфраструктура | Docker, Docker Compose |
| Тесты | pytest |

## Архитектура

Клиент отправляет запрос на рендеринг через REST API. Задача передаётся в очередь фоновой обработки, а клиент может отслеживать её состояние через API или WebSocket. Готовые результаты сохраняются в файловом хранилище, а игровые рейтинги предоставляются через отдельные endpoints.


## Настройка окружения

Создайте локальный `.env` в корне проекта. Не коммитьте его в Git. Пример ниже содержит только локальные значения-заглушки:

```dotenv
DEBUG=false

SECRET_KEY=replace-with-a-long-random-secret
JWT_SECRET_KEY=replace-with-another-long-random-secret
JWT_ISSUER=my-api
JWT_AUDIENCE=my-frontend

DB_NAME=retro_streamer
DB_USER=retro_streamer
DB_PASSWORD=change-this-password
DB_HOST=db
DB_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379

S3_KEY_ID=minioadmin
S3_SECRET=change-this-minio-password
S3_INTERNAL_URL=http://minio:9000
S3_EXTERNAL_URL=http://localhost:9000
S3_PUBLIC_BUCKET=retro-streamer-public
S3_PRIVATE_BUCKET=retro-streamer-private

COOKIE_SECURE=false
COOKIE_SAMESITE=lax
CURRENT_SEASON_ID=1
```

Имена параметров соответствуют настройкам приложения; перед запуском сверьте их с `app/core/config.py` и текущей конфигурацией `docker-compose.yml`. Для production используйте уникальные секреты, включите HTTPS и настройте secure cookies. Значения `minioadmin` допустимы только для локальной разработки.

## Запуск

**Требования:** установленный Docker и Docker Compose.

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/ValeriaPostylyakova/retro-streamer.git
   cd Retro-Streamer
   ```

2. Проверьте настройки окружения и переменные, необходимые сервисам, согласно конфигурации проекта.
3. Запустите приложение:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
```

4. Откройте документацию API:

   - **Swagger UI:** http://localhost:8000/docs
   - **ReDoc:** http://localhost:8000/redoc

   Фактические адреса и доступность интерфейсов зависят от настроек проекта.

Для остановки контейнеров используйте:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml down
```

## Документация

- [Демонстрация Swagger UI](docs/SWAGGER_DEMO.md)

## Что демонстрирует проект

Retro-Streamer показывает практическую работу с несколькими важными аспектами backend-разработки:

- проектирование REST API и разделение ответственности между компонентами;
- аутентификацию и защищённые endpoints;
- выполнение длительных операций вне основного HTTP-запроса;
- взаимодействие через WebSocket;
- работу с реляционной базой данных, очередью задач и объектным хранилищем;
- контейнеризацию и автоматизированное тестирование.
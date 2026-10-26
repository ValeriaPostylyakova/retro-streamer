# Retro Streamer

Backend-сервис для запуска ретро-игр, асинхронной генерации GIF-прохождений и публикации результатов в таблице лидеров.

## Возможности

- Регистрация, вход, обновление и отзыв сессии авторизации.
- Поддержка четырёх игр: Snake, 2048, Labyrinth и Sokoban.
- Получение правил и начального состояния игры по `seed`.
- Асинхронная генерация игровых GIF через Celery.
- Проверка статуса фоновой задачи через REST API и получение обновлений по WebSocket.
- Хранение метаданных в PostgreSQL, кеширование и брокер задач на Redis.
- Загрузка готовых файлов в S3-совместимое хранилище MinIO и выдача временных ссылок на скачивание.
- Таблица лидеров с фильтрацией по игре, сезону и seed.
- Миграции схемы БД через Alembic.
- Docker Compose для локального запуска зависимостей и приложения.

## Технологии

- Python 3.12
- FastAPI, Uvicorn, Pydantic
- SQLAlchemy 2.x, asyncpg, PostgreSQL 16
- Alembic
- Redis 7
- Celery и Flower
- MinIO / S3 API, boto3, aioboto3
- JWT, pwdlib/Argon2
- Docker Compose
- pytest и httpx

## Архитектура

```text
Клиент
  └── FastAPI (/api/v1)
       ├── Auth — регистрация и авторизация
       ├── Game — запросы на рендеринг, статусы и скачивание
       ├── WebSocket — обновления статуса задачи
       └── Leaderboard — таблица результатов

FastAPI ── PostgreSQL — пользователи, игровые результаты, лидерборд
        ├─ Redis — кеш и брокер/результаты Celery
        ├─ Celery worker — генерация GIF
        └─ MinIO — хранение готовых медиафайлов

Flower — веб-интерфейс мониторинга Celery
```

## Быстрый запуск через Docker Compose

### 1. Требования

- Docker Engine
- Docker Compose plugin (`docker compose`)
- Свободные порты `8000`, `5555`, `5433`, `6379`, `9000`, `9001`

### 2. Настройка окружения

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
S3_ENDPOINT_URL=http://minio:9000
S3_PUBLIC_BUCKET=retro-streamer-public
S3_PRIVATE_BUCKET=retro-streamer-private

COOKIE_SECURE=false
COOKIE_SAMESITE=lax
CURRENT_SEASON_ID=1
```

Имена параметров соответствуют настройкам приложения; перед запуском сверьте их с `app/core/config.py` и текущей конфигурацией `docker-compose.yml`. Для production используйте уникальные секреты, включите HTTPS и настройте secure cookies. Значения `minioadmin` допустимы только для локальной разработки.

### 3. Запуск

Из каталога проекта выполните:

```bash
docker compose up --build
```

Compose запускает PostgreSQL, Redis, MinIO, миграции Alembic, FastAPI, Celery worker и Flower.

Если контейнеры запущены, но API не отвечает, проверьте логи:

```bash
docker compose ps
docker compose logs -f fastapi_server
docker compose logs -f migrations
docker compose logs -f celery_worker
```

Остановка:

```bash
docker compose down
```

Остановка с удалением данных PostgreSQL, Redis и MinIO (необратимо):

```bash
docker compose down -v
```

### 4. Интерфейсы

- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- Flower: <http://localhost:5555>
- MinIO Console: <http://localhost:9001>
- PostgreSQL с хоста: `localhost:5433`
- Redis с хоста: `localhost:6379`
- MinIO S3 API: <http://localhost:9000>

Порты и адреса приведены по текущему `docker-compose.yml`; фактическая доступность зависит от успешного старта контейнеров.

## REST API

Все REST-маршруты имеют префикс `/api/v1`. Актуальные схемы запросов и ответов смотрите в Swagger UI.

| Метод | Путь | Назначение |
|---|---|---|
| `POST` | `/auth/register` | Регистрация пользователя |
| `POST` | `/auth/login` | Вход и выдача access token |
| `POST` | `/auth/refresh` | Обновление пары токенов через refresh cookie |
| `POST` | `/auth/logout` | Завершение сессии |
| `GET` | `/game/info/{game_name}?seed={seed}` | Правила и начальное состояние игры |
| `POST` | `/game/render` | Запуск генерации прохождения |
| `GET` | `/game/tasks/{task_id}` | Получение статуса фоновой задачи |
| `GET` | `/game/download/{render_id}` | Перенаправление на временную ссылку скачивания |
| `GET` | `/leaderboard/{game_name}?season_id={id}&seed={seed}` | Получение таблицы лидеров |
| WebSocket | `/game/stream/{task_id}?token={access_token}` | Обновления статуса задачи |

### Поддерживаемые идентификаторы игр

- `snake`
- `2048`
- `labyrinth`
- `sokoban`

Для `/game/info/{game_name}` обязателен параметр `seed`. Для таблицы лидеров обязательны `season_id` и `seed`; пагинация задаётся через `limit` (1–100, по умолчанию 20) и `offset` (по умолчанию 0).

### Пример работы с API

Сначала зарегистрируйтесь или войдите через `/api/v1/auth/register` или `/api/v1/auth/login`. Затем откройте `/docs`, чтобы отправить запрос на получение информации об игре и проверить точную структуру `RenderRequest` для выбранной игры.

Пример получения состояния Snake:

```bash
curl "http://localhost:8000/api/v1/game/info/snake?seed=42" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Формат тела для `POST /api/v1/game/render` зависит от выбранной игры и описан в Swagger через дискриминируемую схему запроса. После запуска задачи используйте возвращённый `task_id` для проверки статуса или подключения к WebSocket.

## Локальный запуск без Docker

1. Установите Python 3.12 и запустите PostgreSQL, Redis и S3-совместимое хранилище отдельно.
2. Создайте и активируйте виртуальное окружение.
3. Установите зависимости.
4. Настройте `.env`: адреса сервисов должны указывать на доступные с вашей машины хосты, а не на имена Compose-сервисов (`db`, `redis`, `minio`).
5. Примените миграции.
6. Запустите API и Celery worker в отдельных терминалах.

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

В другом терминале, с активированным тем же окружением:

```bash
celery -A app.core.celery_app worker --loglevel=info
```

Для Flower:

```bash
celery -A app.core.celery_app flower --port=5555
```

Для локального запуска нужно также убедиться, что MinIO доступен, а бакеты, используемые приложением, созданы. Автоматическое создание бакетов при старте в текущем README не предполагается.

## Миграции и тесты

Применить миграции:

```bash
alembic upgrade head
```

Посмотреть текущую ревизию:

```bash
alembic current
```

Зависимости для тестирования указаны в `requirements.txt`. Если тесты добавлены в проект, их можно запустить командой:

```bash
pytest
```

В поставленном архиве не обнаружен отдельный набор тестов самого приложения; наличие pytest в зависимостях само по себе не означает, что покрытие уже реализовано.

## Структура проекта

```text
app/
├── api/v1/                 # REST и WebSocket endpoints
├── auth/                   # модели, схемы и сервисы авторизации
├── core/                   # конфигурация, БД, Redis, S3, Celery, security
├── dependencies/           # общие зависимости, в том числе rate limiting
├── game_renders/
│   ├── engines/            # игровые движки
│   ├── games/              # логика четырёх игр
│   ├── schemas/             # входные и выходные модели
│   ├── services/           # сценарии рендеринга и WebSocket
│   ├── tasks/              # фоновые задачи Celery
│   └── utils/              # генерация GIF и прогресс
├── leaderboard/            # лидерборд
├── schemas/                 # общие схемы API
├── seeds/                   # генерация демонстрационных данных
└── main.py                  # создание FastAPI-приложения
migrations/                  # миграции Alembic
Dockerfile
docker-compose.yml
requirements.txt
```

## Известные ограничения и рекомендации

- Текущая конфигурация Compose ориентирована на разработку: используется `--reload`, код монтируется внутрь контейнера, а секреты задаются через `.env`.
- Перед публичным развёртыванием проверьте CORS: приложение сейчас разрешает `*` вместе с credentials. Для production задайте явный список доверенных origin.
- В `app/core/config.py` заданы значения секретов по умолчанию. В production приложение должно завершать запуск при отсутствующих/слабых секретах, а не использовать значения-заглушки.
- Убедитесь, что MinIO-бакеты созданы и корректно настроены на чтение/скачивание; проверьте конфигурацию public/private bucket.
- Добавьте интеграционные тесты для авторизации, изоляции задач между пользователями, Celery, MinIO и лидерборда.
- Зафиксируйте зависимости и настройте CI (линтер, форматтер, тесты, проверка миграций).
- Не включайте в репозиторий `.env`, `.venv`, `.git` и `__pycache__`; проверьте историю Git на случайно сохранённых секретов.
- Проверьте политику логирования: `echo=True` у SQLAlchemy может выводить SQL и чувствительные данные в логи.
- Проверьте согласованность синхронного и асинхронного доступа к БД, обработку ошибок фоновых задач и сроки жизни временных ссылок.


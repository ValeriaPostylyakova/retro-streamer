from typing import Any

TAGS_METADATA: list[dict[str, Any]] = [
    {
        "name": "auth",
        "description": "Аутентификация пользователей и управление сессиями.",
    },
    {
        "name": "game",
        "description": "Информация об играх, управление задачами рендеринга и скачивание файлов.",
    },
    {"name": "leaderboard", "description": "Публичные рейтинги игроков."},
]

APP_DESCRIPTION = (
    "Backend-сервис для запуска ретро-игр, асинхронной генерации "
    "GIF-прохождений и ведения таблицы лидеров."
)

_VALIDATION_ERROR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "detail": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "loc": {
                        "type": "array",
                        "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                    },
                    "msg": {"type": "string"},
                    "input": {},
                    "ctx": {"type": "object"},
                },
                "required": ["type", "loc", "msg"],
            },
        }
    },
    "required": ["detail"],
}

_DETAIL_STRING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"detail": {"type": "string"}},
    "required": ["detail"],
}

WWW_AUTHENTICATE_HEADER: dict[str, Any] = {
    "WWW-Authenticate": {
        "description": "Схема аутентификации.",
        "schema": {"type": "string", "example": "Bearer"},
    }
}

SET_REFRESH_COOKIE_HEADER: dict[str, Any] = {
    "Set-Cookie": {
        "description": "Установка HttpOnly-cookie `refresh_token`.",
        "schema": {
            "type": "string",
            "example": "refresh_token=...; HttpOnly; Max-Age=604800; Path=/; SameSite=lax; Secure",
        },
    }
}

DELETE_REFRESH_COOKIE_HEADER: dict[str, Any] = {
    "Set-Cookie": {
        "description": "Удаление cookie `refresh_token`.",
        "schema": {
            "type": "string",
            "example": 'refresh_token=""; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/; HttpOnly; SameSite=lax',
        },
    }
}


def validation_error(examples: dict[str, tuple[str, list[dict[str, Any]]]]) -> dict:
    return {
        "description": "Ошибка валидации запроса.",
        "content": {
            "application/json": {
                "schema": _VALIDATION_ERROR_SCHEMA,
                "examples": {
                    key: {"summary": summary, "value": {"detail": detail}}
                    for key, (summary, detail) in examples.items()
                },
            }
        },
    }


def detail_error(
    description: str,
    examples: dict[str, tuple[str, Any]],
    headers: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None,
) -> dict:
    response: dict[str, Any] = {
        "description": description,
        "content": {
            "application/json": {
                "schema": schema or _DETAIL_STRING_SCHEMA,
                "examples": {
                    key: {"summary": summary, "value": {"detail": detail}}
                    for key, (summary, detail) in examples.items()
                },
            }
        },
    }
    if headers:
        response["headers"] = headers
    return response


def ok_examples(
    description: str,
    examples: dict[str, tuple[str, Any]],
    headers: dict[str, Any] | None = None,
) -> dict:
    response: dict[str, Any] = {
        "description": description,
        "content": {
            "application/json": {
                "examples": {
                    key: {"summary": summary, "value": value}
                    for key, (summary, value) in examples.items()
                }
            }
        },
    }
    if headers:
        response["headers"] = headers
    return response


UNAUTHORIZED_BEARER = detail_error(
    "Пользователь не аутентифицирован или токен недействителен.",
    {
        "missing_token": ("Нет заголовка Authorization", "Not authenticated"),
        "invalid_token": (
            "Токен недействителен или просрочен",
            "Could not validate credentials",
        ),
    },
    headers=WWW_AUTHENTICATE_HEADER,
)

EXAMPLE_USER_ID = "3f2b8c1e-7a4d-4e1b-9c55-1d2e3f4a5b6c"
EXAMPLE_ACCESS_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy-payload.dummy-signature"
)
EXAMPLE_TASK_ID = "6f1c2f0e-8d5b-4a52-9d2f-3b7e0c8a1f44"
EXAMPLE_RENDER_ID = "b7a1c0de-52e4-4c6a-8f0e-9d3a7c2b1e55"
EXAMPLE_DOWNLOAD_URL = "http://localhost:9000/games/snake/example.gif"

EXAMPLE_USER_RESPONSE = {
    "tokens": {"access_token": EXAMPLE_ACCESS_TOKEN, "token_type": "bearer"},
    "user": {"id": EXAMPLE_USER_ID, "email": "player@example.com", "role": "default"},
}

GAME_INFO_EXAMPLES: dict[str, tuple[str, Any]] = {
    "snake": (
        "Snake, seed=5",
        {
            "game_name": "snake",
            "seed": 5,
            "rules": {
                "field_size": 20,
                "max_commands": 250,
                "opposite_directions": {
                    "up": "down",
                    "down": "up",
                    "left": "right",
                    "right": "left",
                },
                "available_commands": ["up", "down", "left", "right"],
            },
            "initial_state": {"snake_body": [[10, 10], [10, 9], [10, 8]]},
        },
    )
}

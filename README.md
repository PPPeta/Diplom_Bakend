# Diplom_Bakend — «Вечная Память»

Backend (REST API) системы управления заказами и сервисными операциями бюро ритуальных услуг **«Вечная Память»**. Дипломный проект.

## Стек

- **Python 3.12**, **FastAPI**
- **SQLAlchemy 2.0** (async) + **Alembic** (миграции)
- **2× PostgreSQL**: `core_db` — оперативные данные, `analytics_db` — аналитика и аудит-лог
- **Redis** — кеш, сессии, refresh-токены
- **JWT** (access/refresh) + **RBAC**
- **Docker Compose**

## Архитектура

```
app/
  core/      # конфиг, безопасность (JWT), RBAC, зависимости
  db/        # подключения к 2× PostgreSQL и Redis, сессии
  models/    # SQLAlchemy-модели
  schemas/   # Pydantic-схемы
  api/v1/    # роутеры по модулям
  services/  # бизнес-логика
  main.py    # точка входа FastAPI
alembic/     # миграции
```

## Роли (RBAC)

| Роль | Доступ |
|---|---|
| Частный клиент / гость | без аккаунта, только заявка |
| Партнёр (страховые, корпоративные, смежные сервисы) | аккаунт, заказы, взаиморасчёты |
| Менеджер | обработка заявок и заказов |
| Исполнитель | назначенные задачи |
| Администратор | пользователи, роли, справочники, аудит |

## Быстрый старт

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Проверка готовности: http://localhost:8000/api/v1/health/ready

Миграции:

```bash
docker compose exec api alembic upgrade head
```

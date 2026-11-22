# main.py — точка входа приложения.
#
# Этот файл НЕ содержит логику работы с задачами.
# Он только собирает FastAPI-приложение:
# 1. Создаёт объект app.
# 2. При старте создаёт таблицы в PostgreSQL.
# 3. Подключает маршруты из routers.py.
# 4. Добавляет простой health-check.
#
# Общая схема работы приложения:
#
# HTTP-запрос клиента
#   -> main.py (FastAPI находит нужный маршрут)
#   -> routers.py (обработчик эндпоинта)
#   -> schemas.py (проверка и описание JSON)
#   -> crud.py (операции с БД)
#   -> models.py (описание таблицы todos)
#   -> database.py (подключение и сессия PostgreSQL)
#
# Для /health база данных не используется.
# Для /todos/ используются routers, schemas, crud, models и database.


# Импортируем декоратор asynccontextmanager.
# Он превращает обычную async-функцию в async context manager.
# Context manager — это конструкция, которую можно использовать с `with`.
# В нашем случае она нужна, чтобы выполнить код:
# - до запуска сервера (создание таблиц);
# - после остановки сервера (закрытие подключений к БД).
from contextlib import asynccontextmanager


# Импортируем главный класс FastAPI.
# На его основе создаётся веб-приложение.
from fastapi import FastAPI


# Импортируем из database.py:
# - Base: базовый класс для SQLAlchemy-моделей.
#   От него наследуется Todo в models.py.
#   Благодаря этому SQLAlchemy знает, какие таблицы нужно создать.
#
# - engine: объект SQLAlchemy, который управляет подключениями к PostgreSQL.
#   Через него создаются соединения и выполняются запросы к БД.
from app.database import Base, engine


# Импортируем router из routers.py.
#
# `as todos_router` — это псевдоним.
# То есть дальше в файле вместо `router` мы пишем `todos_router`.
# Это сделано только для более понятного имени переменной.
from app.routers import router as todos_router


# Декоратор превращает функцию lifespan в async context manager.
#
# lifespan — это функция жизненного цикла приложения.
# FastAPI вызывает её:
# 1. Один раз при запуске приложения.
# 2. Один раз при остановке приложения.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup, dispose engine on shutdown."""

    # engine.begin() открывает соединение с PostgreSQL
    # и начинает транзакцию.
    #
    # `as conn` даёт этому соединению имя conn.
    #
    # `async with` гарантирует, что после блока соединение
    # будет корректно закрыто, даже если произошла ошибка.
    async with engine.begin() as conn:

        # Base.metadata — реестр всех SQLAlchemy-моделей,
        # которые наследуются от Base.
        #
        # В нашем проекте там находится модель Todo.
        # Поэтому SQLAlchemy знает, что нужно создать таблицу todos.
        #
        # create_all создаёт таблицы, которых ещё нет.
        # Если таблица уже существует, она не будет пересоздана.
        #
        # ВАЖНО: create_all — синхронная функция SQLAlchemy.
        # Но у нас асинхронный engine, поэтому используется run_sync.
        #
        # run_sync позволяет выполнить синхронную операцию SQLAlchemy
        # внутри асинхронного соединения.
        await conn.run_sync(Base.metadata.create_all)


    # yield — граница между запуском и остановкой приложения.
    #
    # Всё, что написано ДО yield, выполняется при старте.
    # Всё, что написано ПОСЛЕ yield, выполняется при остановке.
    #
    # Пока FastAPI находится "на yield",
    # сервер работает и принимает HTTP-запросы.
    yield


    # Когда приложение останавливается,
    # engine.dispose() закрывает подключения к PostgreSQL.
    #
    # Это нужно, чтобы не оставлять открытые соединения
    # и не удерживать ресурсы после завершения работы.
    await engine.dispose()


# Создаём объект FastAPI-приложения.
#
# title и version отображаются в автоматической документации Swagger:
# обычно она доступна по адресу http://localhost:8000/docs
#
# lifespan=lifespan говорит FastAPI:
# "при старте и остановке приложения вызывай функцию lifespan".
app = FastAPI(title="Todo API", version="1.0.0", lifespan=lifespan)


# Подключаем маршруты из routers.py к основному приложению.
#
# Без этой строки эндпоинты /todos/... не будут доступны.
#
# В routers.py маршруты существуют внутри переменной router:
# POST /todos/
# GET /todos/
# GET /todos/{todo_id}
# PUT /todos/{todo_id}
# DELETE /todos/{todo_id}
#
# include_router встраивает их в app.
app.include_router(todos_router)


# Декоратор @app.get означает:
# "когда придёт GET-запрос на /health, вызови функцию health()".
#
# Это простой health-check: он показывает,
# что приложение запущено и отвечает на запросы.
#
# База данных здесь не используется.
@app.get("/health")
async def health():
    """Liveness probe."""

    # FastAPI автоматически превратит этот словарь в JSON:
    # {"status": "ok"}
    #
    # Клиент получит HTTP-статус 200 OK.
    return {"status": "ok"}


# Пример запроса:
#
# GET http://localhost:8000/health
#
# Путь запроса:
#
# Клиент отправляет GET /health
# -> FastAPI ищет маршрут GET /health
# -> находит функцию health()
# -> вызывает её
# -> получает {"status": "ok"}
# -> превращает словарь в JSON
# -> отправляет клиенту ответ 200 OK
#
# В этом запросе НЕ участвуют:
# database.py, crud.py, models.py, schemas.py.
#
# А вот для GET /todos/ путь будет таким:
#
# Клиент отправляет GET /todos/
# -> main.py находит маршрут GET /todos/
# -> routers.py вызывает list_todos()
# -> database.py через Depends(get_db) создаёт AsyncSession
# -> routers.py вызывает crud.get_todos(db, skip=0, limit=100)
# -> crud.py выполняет SELECT из таблицы todos
# -> PostgreSQL возвращает строки
# -> SQLAlchemy превращает строки в объекты Todo
# -> schemas.TodoOut превращает объекты в JSON
# -> FastAPI отправляет JSON клиенту
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas


async def get_todos(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[models.Todo]:
    """Return a paginated list of todos."""
    result = await db.execute(select(models.Todo).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_todo(db: AsyncSession, todo_id: int) -> Optional[models.Todo]:
    """Return a single todo or None."""
    result = await db.execute(select(models.Todo).where(models.Todo.id == todo_id))
    return result.scalar_one_or_none()


async def create_todo(db: AsyncSession, todo: schemas.TodoCreate) -> models.Todo:
    """Insert a new todo and return it."""
    db_todo = models.Todo(**todo.model_dump())
    db.add(db_todo)
    await db.commit()
    await db.refresh(db_todo)
    return db_todo


async def update_todo(
    db: AsyncSession, todo_id: int, todo: schemas.TodoUpdate
) -> Optional[models.Todo]:
    """Apply partial updates to an existing todo. Returns None if not found."""
    db_todo = await get_todo(db, todo_id)
    if db_todo is None:
        return None
    for key, value in todo.model_dump(exclude_unset=True).items():
        setattr(db_todo, key, value)
    await db.commit()
    await db.refresh(db_todo)
    return db_todo


async def delete_todo(db: AsyncSession, todo_id: int) -> bool:
    """Delete a todo. Returns True if deleted, False if not found."""
    db_todo = await get_todo(db, todo_id)
    if db_todo is None:
        return False
    await db.delete(db_todo)
    await db.commit()
    return True
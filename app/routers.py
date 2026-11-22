from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("/", response_model=schemas.TodoOut, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo: schemas.TodoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new todo item."""
    return await crud.create_todo(db, todo)


@router.get("/", response_model=List[schemas.TodoOut])
async def list_todos(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List todos with pagination."""
    return await crud.get_todos(db, skip=skip, limit=limit)


@router.get("/{todo_id}", response_model=schemas.TodoOut)
async def get_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single todo by id."""
    todo = await crud.get_todo(db, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=schemas.TodoOut)
async def update_todo(
    todo_id: int,
    todo: schemas.TodoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Partially update a todo (PATCH-like semantics on PUT)."""
    updated = await crud.update_todo(db, todo_id, todo)
    if updated is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return updated


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    todo_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a todo by id."""
    deleted = await crud.delete_todo(db, todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Todo not found")
    return None
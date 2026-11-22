from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import router as todos_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup, dispose engine on shutdown."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Todo API", version="1.0.0", lifespan=lifespan)

app.include_router(todos_router)


@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok"}
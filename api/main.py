from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.Database import engine
from api.models import Base
from api.routes.routes import router


# ── Create tables on startup ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Financial Research API",
    description="Multi-agent LangGraph pipeline with JWT auth and PostgreSQL.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(router)

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "AI Financial Research API is running."}
"""MAEP-CN FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent_sdk.db import DBClient
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path = getattr(app.state, "db_path", "maep.db")
    app.state.db = DBClient(db_path=db_path)
    yield
    app.state.db.close()


def create_app(db_path: str = "maep.db") -> FastAPI:
    app = FastAPI(
        title="MAEP-CN",
        description="多智能体执行协议（中国版）— 基于预付费余额的可信智能体协作协议",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.db_path = db_path

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    web_dir = Path(__file__).resolve().parent.parent / "web"
    if web_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

    return app

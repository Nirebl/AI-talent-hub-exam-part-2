from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request

from support_ai.infrastructure.api.dependencies import (
    get_container,
    reset_container,
)
from support_ai.infrastructure.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = get_container()
    yield
    reset_container()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Support Ticket AI",
        version="0.4.0",
        description=(
            "PoC API for support-ticket classification, "
            "risk-aware routing and asynchronous answer generation."
        ),
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_metrics(request: Request, call_next):
        started = perf_counter()
        response = await call_next(request)
        container = get_container()
        container.metrics.observe(
            "http.request_ms",
            (perf_counter() - started) * 1000,
        )
        container.metrics.increment(
            f"http.status.{response.status_code}"
        )
        return response

    app.include_router(router)
    return app


app = create_app()

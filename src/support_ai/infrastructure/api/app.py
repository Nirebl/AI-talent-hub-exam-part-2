from fastapi import FastAPI

from support_ai.infrastructure.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Support Ticket AI",
        version="0.2.0",
        description=(
            "PoC API for support-ticket classification, "
            "risk-aware routing and asynchronous answer generation."
        ),
    )
    app.include_router(router)
    return app


app = create_app()

import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.logging_config import setup_logging, request_id_ctx
from app.utils.errors import (
    AppError,
    app_error_handler,
    validation_error_handler,
    http_error_handler,
    generic_error_handler
)
from app.api.v1.router import api_router

setup_logging(settings.LOG_LEVEL)

def create_app() -> FastAPI:
    app = FastAPI(
        title="TuneChecker API",
        description="Sales Call Quality Analysis Agent API",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json"
    )

    # CORS
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"]
    )

    # Request ID Middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:8]}"
        token = request_id_ctx.set(req_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)

    # Register Exception Handlers
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)

    # Include API Routers
    app.include_router(api_router, prefix="/api/v1")

    return app

app = create_app()

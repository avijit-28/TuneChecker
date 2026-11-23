import uuid
from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.logging_config import request_id_ctx

class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        retryable: bool = False,
        details: Optional[dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details or {}
        super().__init__(message)

def make_error_payload(code: str, message: str, retryable: bool, details: dict, request_id: str) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "details": details,
            "request_id": request_id
        }
    }

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    req_id = request_id_ctx.get() or f"req_{uuid.uuid4().hex[:8]}"
    return JSONResponse(
        status_code=exc.status_code,
        content=make_error_payload(exc.code, exc.message, exc.retryable, exc.details, req_id),
        headers={"X-Request-ID": req_id}
    )

async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    req_id = request_id_ctx.get() or f"req_{uuid.uuid4().hex[:8]}"
    errors = exc.errors()
    details = {"errors": [{"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")} for e in errors]}
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=make_error_payload("REQUEST_INVALID", "Request parameters or body failed validation.", False, details, req_id),
        headers={"X-Request-ID": req_id}
    )

async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    req_id = request_id_ctx.get() or f"req_{uuid.uuid4().hex[:8]}"
    code_map = {
        404: "NOT_FOUND",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        405: "METHOD_NOT_ALLOWED",
        413: "FILE_TOO_LARGE",
        415: "INVALID_FILE_TYPE",
        429: "TOO_MANY_REQUESTS",
        503: "SERVICE_UNAVAILABLE"
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content=make_error_payload(code, str(exc.detail), False, {}, req_id),
        headers={"X-Request-ID": req_id}
    )

async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    req_id = request_id_ctx.get() or f"req_{uuid.uuid4().hex[:8]}"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=make_error_payload("INTERNAL_ERROR", "An unexpected internal server error occurred.", False, {}, req_id),
        headers={"X-Request-ID": req_id}
    )

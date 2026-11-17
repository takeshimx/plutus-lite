import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import summary, transactions

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("plutus_lite.access")


def create_app() -> FastAPI:
    app = FastAPI(title="Plutus Lite API", version="0.1.0")
    settings = get_settings()

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @app.middleware("http")
    async def access_log(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # リクエストIDと UID だけを記録する。メール、トークン、メモは記録しない
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        started = time.perf_counter()
        response = await call_next(request)
        logger.info(
            "request_id=%s method=%s path=%s status=%s uid=%s ms=%d",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            getattr(request.state, "uid", "-"),
            (time.perf_counter() - started) * 1000,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # 入力の誤りは 422 ではなく 400 で返す(A5)
        errors = [{k: v for k, v in e.items() if k in ("loc", "msg", "type")} for e in exc.errors()]
        return JSONResponse(status_code=400, content={"detail": jsonable_encoder(errors)})

    # Cloud Run では /healthz が Google 側で予約されていて届かないため、/health も用意する
    @app.get("/health", include_in_schema=False)
    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(transactions.router)
    app.include_router(summary.router)
    return app


app = create_app()

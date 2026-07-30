import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.database.session import engine

REQUEST_COUNT = Counter(
    "fastapi_http_requests_total",
    "Total HTTP requests processed by the FastAPI application.",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "fastapi_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
)

DB_CONNECTION_UP = Gauge(
    "fastapi_db_connection_up",
    "Whether the FastAPI application can connect to the database.",
)

# 트래픽 제외(/metrics, health check)
EXCLUDED_METRIC_PATHS = {
    "/metrics",
    "/api/health",
    "/api/health/db",
}


def _join_route_paths(prefix: str, path: str) -> str:
    if path == "/":
        return f"{prefix.rstrip('/')}/" if prefix else "/"
    if not prefix:
        return path
    return f"{prefix.rstrip('/')}/{path.lstrip('/')}"


def _build_route_template_map(
    routes: list[Any],
    prefix: str = "",
) -> dict[Callable[..., Any], str]:
    route_templates: dict[Callable[..., Any], str] = {}

    for route in routes:
        original_router = getattr(route, "original_router", None)
        include_context = getattr(route, "include_context", None)
        if original_router is not None and include_context is not None:
            included_prefix = getattr(include_context, "prefix", "")
            nested_prefix = _join_route_paths(prefix, included_prefix)
            route_templates.update(
                _build_route_template_map(original_router.routes, nested_prefix),
            )
            continue

        endpoint = getattr(route, "endpoint", None)
        route_path = getattr(route, "path", None)
        if endpoint is not None and isinstance(route_path, str):
            route_templates[endpoint] = _join_route_paths(prefix, route_path)

    return route_templates


def _get_route_template(request: Request) -> str | None:
    route_templates = getattr(request.app.state, "route_templates", None)
    if route_templates is None:
        route_templates = _build_route_template_map(request.app.routes)
        request.app.state.route_templates = route_templates

    endpoint = request.scope.get("endpoint")
    return route_templates.get(endpoint)


def _normalize_path(request: Request) -> str:
    route_template = _get_route_template(request)
    if route_template is not None:
        return route_template
    return request.url.path


def _update_db_connection_metric() -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        DB_CONNECTION_UP.set(0)
    else:
        DB_CONNECTION_UP.set(1)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # 내부 모니터링/헬스체크는 Prometheus metric에 기록하지 않는다.
        if request.url.path in EXCLUDED_METRIC_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        method = request.method

        try:
            response = await call_next(request)
        except Exception:
            # 예외도 500으로 집계
            path = _normalize_path(request)  # 요청
            REQUEST_COUNT.labels(
                method=method,
                path=path,
                status_code="500",
            ).inc()
            REQUEST_LATENCY.labels(
                method=method,
                path=path,
            ).observe(time.perf_counter() - start_time)
            raise

        path = _normalize_path(request)
        REQUEST_COUNT.labels(
            method=method,
            path=path,
            status_code=str(response.status_code),
        ).inc()
        REQUEST_LATENCY.labels(
            method=method,
            path=path,
        ).observe(time.perf_counter() - start_time)
        return response


def metrics_response(request: Request) -> Response:
    _update_db_connection_metric()

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

import time

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


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


def _normalize_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str):
        return path
    return request.url.path


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        start_time = time.perf_counter()
        method = request.method
        path = _normalize_path(request)

        try:
            response = await call_next(request)
        except Exception:
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
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

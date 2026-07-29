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

# 트래픽 제외(/metrics, health check)
EXCLUDED_METRIC_PATHS = {
    "/metrics",
    "/api/health",
    "/api/health/db",
}


def _normalize_path(request: Request) -> str:
    path = request.url.path
    path_params = request.path_params
    if not path_params:
        return path

    normalized_segments = []
    for segment in path.split("/"):
        normalized_segment = segment
        for param_name, param_value in path_params.items():
            if segment == str(param_value):
                normalized_segment = f"{{{param_name}}}"
                break
        normalized_segments.append(normalized_segment)
    return "/".join(normalized_segments)


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
            path = _normalize_path(request) # 요청
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
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )

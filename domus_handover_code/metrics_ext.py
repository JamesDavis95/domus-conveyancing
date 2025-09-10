import time
from typing import Callable, Iterable, Optional
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    'domus_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status']
)
REQUEST_LATENCY = Histogram(
    'domus_request_latency_seconds',
    'Latency of HTTP requests in seconds',
    ['method', 'path']
)

SKIP_PATHS_DEFAULT = {"/metrics", "/health", "/ready", "/docs", "/openapi.json"}

class MetricsMiddleware:
    def __init__(self, app, skip_paths: Optional[Iterable[str]] = None):
        self.app = app
        self.skip = set(skip_paths or SKIP_PATHS_DEFAULT)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)

        path = scope.get('path', '/')
        method = scope.get('method', 'GET')

        if path in self.skip:
            return await self.app(scope, receive, send)

        start = time.time()
        status_holder = {'code': '000'}

        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                status_holder['code'] = str(message['status'])
                REQUEST_COUNT.labels(method=method, path=path, status=status_holder['code']).inc()
            return await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            REQUEST_LATENCY.labels(method=method, path=path).observe(time.time() - start)

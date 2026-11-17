import re
import time
import uuid

from fastapi import FastAPI, Request

# Allow only safe characters: an id gets copied into logs and headers,
# so we never trust raw client input there.
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def register_middleware(app: FastAPI) -> None:

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        # Way IN: reuse a valid id sent by a proxy or client, otherwise make one 
        incoming = request.headers.get("x-request-id", "")
        request_id = (
            incoming if REQUEST_ID_PATTERN.match(incoming) else uuid.uuid4().hex
        )
        request.state.request_id = request_id

        start = time.perf_counter()  # monotonic clock, made for measuring durations
        response = await call_next(
            request
        )  # everything after this layer: CORS, router, our route...
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Way OUT: stamp the response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
        return response

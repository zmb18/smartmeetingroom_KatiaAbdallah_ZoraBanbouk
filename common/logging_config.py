import logging
from time import time
from fastapi import Request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def setup_request_logging(app):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time()
        response = await call_next(request)
        duration_ms = int((time() - start) * 1000)
        logging.info("%s %s -> %s (%d ms)", request.method, request.url.path, response.status_code, duration_ms)
        return response

    return app

import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Request
import time

# Configure a rotating log file
def setup_request_logging(app: FastAPI):
    # Logger for all app events
    logger = logging.getLogger("users_service")
    logger.setLevel(logging.INFO)

    # Rotating file: 5 MB per file, keep 3 backups
    handler = RotatingFileHandler("users_service.log", maxBytes=5*1024*1024, backupCount=3)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Middleware to log each request
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"{request.client.host} - {request.method} {request.url.path} "
            f"Status: {response.status_code} - {process_time:.2f}ms"
        )
        return response

    return logger

import sys
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logger(log_level: str = "INFO") -> None:
    """Configures Loguru handlers: console (colored) and rotating file."""
    # Remove all default handlers
    logger.remove()

    # Console Handler (clean and readable)
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        enqueue=True,
    )

    # Ensure logs directory exists
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "trading.log"

    # Rotating File Handler
    logger.add(
        str(log_file),
        level=log_level,
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )


def log_api_call(
    endpoint: str,
    payload: dict,
    response: Optional[dict] = None,
    latency_ms: Optional[float] = None,
    error: Optional[str] = None,
    retry_count: int = 0
) -> None:
    """Helper to log API client details in a structured way."""
    message = (
        f"API Call | Endpoint: {endpoint} | "
        f"Payload: {payload} | "
        f"Response: {response if response else 'None'} | "
        f"Latency: {f'{latency_ms:.2f}ms' if latency_ms is not None else 'N/A'} | "
        f"Retries: {retry_count}"
    )
    if error:
        message += f" | Error: {error}"
        logger.error(message)
    else:
        logger.info(message)

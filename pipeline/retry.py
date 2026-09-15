"""
Robust retry utility with exponential backoff and jitter for external network calls.
Handles transient failures in Vercel, Midtrans, and web scraping operations.
"""

import time
import random
import functools
from typing import Callable, Any, Tuple, Type
from pipeline.logging_config import get_logger

logger = get_logger("retry")


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,)
) -> Callable:
    """Decorator to retry a function on exception with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_err = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    if attempt == max_attempts:
                        logger.error("Function '%s' failed after %d attempts: %s", func.__name__, max_attempts, e)
                        raise

                    sleep_time = delay
                    if jitter:
                        sleep_time += random.uniform(0, 0.5 * delay)

                    logger.warning(
                        "Attempt %d/%d failed for '%s': %s. Retrying in %.2fs...",
                        attempt, max_attempts, func.__name__, e, sleep_time
                    )
                    time.sleep(sleep_time)
                    delay *= backoff_factor

            raise last_err
        return wrapper
    return decorator


def retry_call(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,)
) -> Any:
    """Executes a callable with retries without decorator syntax."""
    if kwargs is None:
        kwargs = {}
    decorated = retry(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        backoff_factor=backoff_factor,
        exceptions=exceptions
    )(func)
    return decorated(*args, **kwargs)

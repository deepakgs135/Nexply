"""Small privacy-safe tracing decorator for backend functions."""

import inspect
import logging
from functools import wraps
from time import perf_counter
from typing import Any, Callable


def debug_trace(function: Callable[..., Any]) -> Callable[..., Any]:
    """Log function entry, completion, duration, and failures without arguments."""
    logger = logging.getLogger(function.__module__)

    if inspect.iscoroutinefunction(function):
        @wraps(function)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            started = perf_counter()
            logger.debug("Entering %s", function.__qualname__)
            try:
                result = await function(*args, **kwargs)
            except Exception:
                logger.exception("Failed %s", function.__qualname__)
                raise
            logger.debug(
                "Completed %s in %.2f ms",
                function.__qualname__,
                (perf_counter() - started) * 1000,
            )
            return result

        return async_wrapper

    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        started = perf_counter()
        logger.debug("Entering %s", function.__qualname__)
        try:
            result = function(*args, **kwargs)
        except Exception:
            logger.exception("Failed %s", function.__qualname__)
            raise
        logger.debug(
            "Completed %s in %.2f ms",
            function.__qualname__,
            (perf_counter() - started) * 1000,
        )
        return result

    return wrapper

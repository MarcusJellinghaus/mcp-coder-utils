"""Shared logging configuration and utilities."""

import json
import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, Union, cast, overload

import structlog
from pythonjsonlogger.json import JsonFormatter

__all__ = ["OUTPUT", "log_function_call", "setup_logging"]

# Type variable for function return types
T = TypeVar("T")

# Custom log level between INFO (20) and WARNING (30)
OUTPUT: int = 25
logging.addLevelName(OUTPUT, "OUTPUT")

# Redaction support
REDACTED_VALUE: str = "***"

RedactableDict = dict[Union[str, tuple[str, ...]], Any]

# Standard log record fields — everything else is considered "extra"
STANDARD_LOG_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "msg",
        "args",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "message",
        "asctime",
        "exc_info",
        "exc_text",
        "taskName",
    }
)

# Create standard logger
stdlogger = logging.getLogger(__name__)


class CleanFormatter(logging.Formatter):
    """Bare CLI output formatter — message only, no timestamp or level."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a plain message string."""
        return record.getMessage()


class ExtraFieldsFormatter(logging.Formatter):
    """Formatter that appends extra fields to the log line."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with any extra fields appended."""
        base = super().format(record)
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in STANDARD_LOG_FIELDS and not k.startswith("_")
        }
        if extras:
            return f"{base} | {extras}"
        return base


def _is_testing_environment() -> bool:
    """Detect if we are running inside a test framework.

    Prevents clearing pytest's logging capture handlers.
    """
    # Check for pytest
    try:
        import _pytest.config  # noqa: F401 — presence check only

        return True
    except ImportError:
        pass

    # Check for unittest
    if "unittest" in os.environ.get("PYTHONDONTWRITEBYTECODE", ""):
        return True

    return False


def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """Configure logging — if *log_file* specified, logs to file; otherwise console.

    Configures structlog globally. Call once at startup;
    repeated calls override the structlog configuration.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    root_logger = logging.getLogger()

    # Preserve pytest capture handlers when running under test frameworks
    if _is_testing_environment():
        for handler in root_logger.handlers[:]:
            if not hasattr(handler, "_store"):  # pytest capture handlers have _store
                root_logger.removeHandler(handler)
    else:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    root_logger.setLevel(numeric_level)

    if log_file:
        # FILE LOGGING ONLY — no console output
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

        json_handler = logging.FileHandler(log_file)
        json_formatter = JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d",
            timestamp=True,
        )
        json_handler.setFormatter(json_formatter)
        root_logger.addHandler(json_handler)

        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        stdlogger.info("Logging initialized: file=%s, level=%s", log_file, log_level)
    else:
        # CONSOLE LOGGING ONLY
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        stdlogger.info("Logging initialized: console=%s", log_level)


def _redact_for_logging(
    params: dict[Any, Any], sensitive_fields: set[str]
) -> dict[Any, Any]:
    """Replace values of *sensitive_fields* with ``REDACTED_VALUE``.

    Supports both simple string keys and tuple keys (for nested paths).
    """
    redacted: RedactableDict = {}
    for key, value in params.items():
        if isinstance(key, tuple):
            # Tuple key — redact if any component is sensitive
            if any(part in sensitive_fields for part in key):
                redacted[key] = REDACTED_VALUE
            else:
                redacted[key] = value
        elif key in sensitive_fields:
            redacted[key] = REDACTED_VALUE
        else:
            redacted[key] = value
    return redacted


@overload
def log_function_call(func: Callable[..., T]) -> Callable[..., T]: ...


@overload
def log_function_call(
    *, sensitive_fields: set[str]
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...


def log_function_call(
    func: Optional[Callable[..., T]] = None,
    *,
    sensitive_fields: Optional[set[str]] = None,
) -> Any:
    """Decorator to log function calls with parameters, timing, and results.

    Can be used bare (``@log_function_call``) or with sensitive-field
    redaction (``@log_function_call(sensitive_fields={"token"})``).
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            func_name = fn.__name__
            module_name = fn.__module__
            line_no = fn.__code__.co_firstlineno

            # Prepare parameters for logging
            log_params: dict[str, Any] = {}

            # Handle method calls (skip self/cls)
            if (
                args
                and hasattr(args[0], "__class__")
                and args[0].__class__.__module__ != "builtins"
            ):
                log_params.update(
                    {
                        k: v
                        for k, v in zip(
                            fn.__code__.co_varnames[1 : len(args)], args[1:]
                        )
                    }
                )
            else:
                log_params.update(
                    {k: v for k, v in zip(fn.__code__.co_varnames[: len(args)], args)}
                )

            # Add keyword arguments
            log_params.update(kwargs)

            # Redact sensitive fields if specified
            if sensitive_fields:
                log_params = _redact_for_logging(log_params, sensitive_fields)

            # Convert Path objects to strings and handle other non-serializable types
            serializable_params: dict[str, Any] = {}
            for k, v in log_params.items():
                key_str = str(k) if not isinstance(k, str) else k
                if isinstance(v, Path):
                    serializable_params[key_str] = str(v)
                else:
                    try:
                        json.dumps(v)
                        serializable_params[key_str] = v
                    except (TypeError, OverflowError):
                        serializable_params[key_str] = str(v)

            # Check if structured logging is enabled
            has_structured = any(
                isinstance(h, logging.FileHandler) for h in logging.getLogger().handlers
            )

            if has_structured:
                structlogger = structlog.get_logger(module_name)
                structlogger.debug(
                    f"Calling function {func_name}",
                    function=func_name,
                    parameters=serializable_params,
                    module=module_name,
                    lineno=line_no,
                )

            stdlogger.debug(
                "Calling %s with parameters: %s",
                func_name,
                json.dumps(serializable_params, default=str),
            )

            # Execute function and measure time
            start_time = time.time()
            try:
                result = fn(*args, **kwargs)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)

                # Prepare result for logging
                result_for_log: Any
                serializable_result: Any
                if isinstance(result, (list, dict)) and len(str(result)) > 1000:
                    result_for_log = (
                        f"<Large result of type {type(result).__name__},"
                        f" length: {len(str(result))}>"
                    )
                    serializable_result = result_for_log
                else:
                    result_for_log = result
                    try:
                        json.dumps(result)
                        serializable_result = result
                    except (TypeError, OverflowError):
                        serializable_result = (
                            str(result) if result is not None else None
                        )

                if has_structured:
                    structlogger.debug(
                        f"Function {func_name} completed",
                        function=func_name,
                        execution_time_ms=elapsed_ms,
                        status="success",
                        result=serializable_result,
                        module=module_name,
                        lineno=line_no,
                    )

                stdlogger.debug(
                    "%s completed in %sms with result: %s",
                    func_name,
                    elapsed_ms,
                    result_for_log,
                )
                return result

            except Exception as e:
                elapsed_ms = round((time.time() - start_time) * 1000, 2)

                if has_structured:
                    structlogger.error(
                        f"Function {func_name} failed",
                        function=func_name,
                        execution_time_ms=elapsed_ms,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        module=module_name,
                        lineno=line_no,
                        exc_info=True,
                    )

                stdlogger.error(
                    "%s failed after %sms with error: %s: %s",
                    func_name,
                    elapsed_ms,
                    type(e).__name__,
                    str(e),
                    exc_info=True,
                )
                raise

        return cast(Callable[..., T], wrapper)

    if func is not None:
        return decorator(func)
    return decorator

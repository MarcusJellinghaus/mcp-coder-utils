"""Shared logging configuration and utilities."""

import asyncio
import json
import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, cast, overload

import structlog
from pythonjsonlogger.json import JsonFormatter

from mcp_coder_utils.redaction import RedactableDict, redact_for_logging

__all__ = [
    "OUTPUT",
    "STANDARD_LOG_FIELDS",
    "CleanFormatter",
    "ExtraFieldsFormatter",
    "log_function_call",
    "setup_logging",
]

# Custom OUTPUT log level (between INFO=20 and WARNING=30)
# OUTPUT is the default CLI threshold. At this threshold, CleanFormatter
# produces bare messages; at INFO/DEBUG, ExtraFieldsFormatter produces
# verbose timestamped output. Use logger.log(OUTPUT, ...) for user-facing
# CLI messages that should be clean at default verbosity.
OUTPUT = 25
logging.addLevelName(OUTPUT, "OUTPUT")

# Type variable for function return types
T = TypeVar("T")

# Standard LogRecord fields to exclude when extracting extra fields
# These are built-in attributes of logging.LogRecord that should not be treated as "extra" data
STANDARD_LOG_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "msg",
        "args",
        "asctime",  # Added by Formatter.format()
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
        "exc_info",
        "exc_text",
        "thread",
        "threadName",
        "taskName",
        "message",
    }
)


class CleanFormatter(logging.Formatter):
    """Formatter for clean CLI output.

    Used when log threshold is OUTPUT. Produces:
    - OUTPUT-level records: bare message (no prefix)
    - WARNING/ERROR/CRITICAL: "LEVEL: message"

    Extra fields (passed via extra={}) are appended as JSON,
    independently of ExtraFieldsFormatter.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record for clean CLI output.

        Args:
            record: The log record to format.

        Returns:
            The formatted log message.
        """
        message = record.getMessage()

        if record.levelno > OUTPUT:
            message = f"{record.levelname}: {message}"

        # Extract extra fields (attributes not in standard LogRecord fields)
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in STANDARD_LOG_FIELDS
        }

        if extra_fields:
            suffix = json.dumps(extra_fields, default=str)
            return f"{message} {suffix}"

        return message


class ExtraFieldsFormatter(logging.Formatter):
    """Formatter that appends extra fields to log messages.

    This formatter extends the standard logging.Formatter to include any
    extra fields passed via the `extra` parameter in logging calls.
    Extra fields are appended to the log message as a JSON object.

    Example:
        >>> formatter = ExtraFieldsFormatter(
        ...     "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ... )
        >>> handler.setFormatter(formatter)
        >>> logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})
        # Output: 2024-01-15 10:30:00 - myapp - INFO - User logged in {"user_id": 123, "ip": "192.168.1.1"}
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record, appending any extra fields as JSON.

        Args:
            record: The log record to format.

        Returns:
            The formatted log message with extra fields appended as JSON.
        """
        # Get the base formatted message
        base_message = super().format(record)

        # Extract extra fields (attributes not in standard LogRecord fields)
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in STANDARD_LOG_FIELDS
        }

        # If there are extra fields, append them as JSON
        if extra_fields:
            # Use default=str to handle non-serializable values
            suffix = json.dumps(extra_fields, default=str)
            return f"{base_message} {suffix}"

        return base_message


# Create standard logger
stdlogger = logging.getLogger(__name__)

# Attribute marker tagged onto every handler setup_logging creates. Handler
# dedup keys on this marker (not isinstance) so setup_logging removes only the
# handlers it added, leaving pytest's LogCaptureHandler and any consumer handler
# untouched. This makes repeated calls idempotent without testing-env special-casing.
_HANDLER_MARKER = "_mcp_coder_utils_handler"


def _parse_level(level: str | int) -> int:
    """Resolve a log level given as a name or number to its numeric value.

    Args:
        level: A logging level as an int (returned unchanged) or a case-
            insensitive level name (e.g. "INFO", "OUTPUT").

    Returns:
        The numeric log level.

    Raises:
        ValueError: If a string level name is not a known logging level.
    """
    if isinstance(level, int):
        return level
    name = level.upper()
    numeric_level = getattr(logging, name, None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.getLevelName(name)  # resolves "OUTPUT"
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    return numeric_level


def setup_logging(
    log_level: str | int,
    log_file: Optional[str] = None,
    console_level: str | int | None = None,
) -> None:
    """Configure logging to a file and/or the console, at independent levels.

    A file sink and a console sink are configured independently and may coexist:

    - ``log_file`` set  -> structured JSON file handler at ``log_level``.
    - ``console_level`` behaviour:
        * ``None`` (default): a console handler is added **iff** no ``log_file``
          is given (fully backwards compatible file-XOR-console behaviour).
        * a level: a console handler at that level is added **in addition to**
          any file handler (dual mode). ``console_level`` may be given without a
          ``log_file`` too, in which case ``log_level`` only sets the root floor
          and the console handler filters at ``console_level``.

    The root logger level is set to ``min(log_level, console_level)`` so records
    are not pre-filtered at the logger below whichever handler threshold is
    lowest; each handler then applies its own level. The file handler keeps its
    explicit ``setLevel(log_level)`` (load-bearing: it keeps sub-threshold
    records out of the file when the root floor sits below ``log_level``).

    The console handler writes to stderr (bare ``StreamHandler()``, no
    ``stream=``) so stdio MCP servers never write to stdout. Its formatter is
    chosen from the **console** level: ``CleanFormatter`` at ``OUTPUT`` or above,
    ``ExtraFieldsFormatter`` below.

    Idempotent: removes only the handlers this function previously added (tagged
    with ``_HANDLER_MARKER``), leaving pytest's capture handler and any consumer
    handler untouched, then attaches fresh sinks. Configures structlog globally.

    Args:
        log_level: Level for the file sink and the default console level.
        log_file: Optional path to a JSON log file.
        console_level: Optional level for a console sink added alongside the file.

    Raises:
        ValueError: If a string level name (``log_level`` or ``console_level``)
            is not a known logging level.
    """
    root_logger = logging.getLogger()

    # Remove ONLY our previously added handlers (marker-based idempotency).
    for handler in root_logger.handlers[:]:
        if getattr(handler, _HANDLER_MARKER, False):
            root_logger.removeHandler(handler)
            handler.close()

    numeric_level = _parse_level(log_level)
    numeric_console_level = (
        _parse_level(console_level) if console_level is not None else numeric_level
    )
    # Root floor sits at the lowest handler threshold so no sink is starved.
    root_logger.setLevel(min(numeric_level, numeric_console_level))

    sinks: list[str] = []

    if log_file:
        # File sink - structured JSON output.
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

        json_handler = logging.FileHandler(log_file)
        json_handler.setLevel(numeric_level)

        # This formatter ensures timestamp and level are included as separate fields in JSON
        json_formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d"
        )
        json_handler.setFormatter(json_formatter)
        setattr(json_handler, _HANDLER_MARKER, True)
        root_logger.addHandler(json_handler)
        sinks.append(f"file={log_file} level={logging.getLevelName(numeric_level)}")

    if console_level is not None or log_file is None:
        # Console sink - added alongside the file when console_level is given, or
        # standalone when no file is configured. Writes to stderr by default.
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_console_level)
        if numeric_console_level >= OUTPUT:
            console_formatter: logging.Formatter = CleanFormatter()
        else:
            console_formatter = ExtraFieldsFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        console_handler.setFormatter(console_formatter)
        setattr(console_handler, _HANDLER_MARKER, True)
        root_logger.addHandler(console_handler)
        sinks.append(f"console level={logging.getLevelName(numeric_console_level)}")

    # Configure structlog once, unconditionally, with the JSON-renderer chain.
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

    stdlogger.debug("Logging initialized: %s", ", ".join(sinks))


# Overload signatures for proper typing
@overload
def log_function_call(func: Callable[..., T]) -> Callable[..., T]: ...


@overload
def log_function_call(
    func: None = None,
    *,
    sensitive_fields: list[str] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...


def log_function_call(
    func: Callable[..., T] | None = None,
    *,
    sensitive_fields: list[str] | None = None,
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to log function calls with parameters, timing, and results.

    Can be used as @log_function_call or @log_function_call(sensitive_fields=[...]).

    Args:
        func: The function to decorate (when used without parentheses).
        sensitive_fields: Optional list of field names whose values should be
            redacted in logs. Applies to both parameters and return values.

    Returns:
        Decorated function or decorator depending on usage.
    """
    sensitive_set = set(sensitive_fields) if sensitive_fields else set()

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        def _log_call_start(
            fn: Callable[..., Any],
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
            sensitive_set: set[str],
        ) -> tuple[logging.Logger, bool, float, str, str, int]:
            func_name = fn.__name__
            module_name = fn.__module__
            line_no = fn.__code__.co_firstlineno

            # Get logger for the decorated function's module (not log_utils)
            func_logger = logging.getLogger(module_name)

            # Prepare parameters for logging
            log_params: dict[str, Any] = {}

            # Handle method calls (skip self/cls)
            if args and fn.__code__.co_varnames[0] in ("self", "cls"):
                log_params.update(
                    dict(zip(fn.__code__.co_varnames[1 : len(args)], args[1:]))
                )
            else:
                log_params.update(dict(zip(fn.__code__.co_varnames[: len(args)], args)))

            # Add keyword arguments
            log_params.update(kwargs)

            # Convert Path objects to strings and handle other non-serializable types
            serializable_params: dict[str, Any] = {}
            for k, v in log_params.items():
                if isinstance(v, Path):
                    serializable_params[k] = str(v)
                else:
                    try:
                        # Test if it's JSON serializable
                        json.dumps(v)
                        serializable_params[k] = v
                    except (TypeError, OverflowError):
                        # If not serializable, convert to string
                        serializable_params[k] = str(v)

            # Apply redaction for sensitive fields
            # Cast needed because serializable_params is dict[str, Any] but
            # redact_for_logging accepts RedactableDict
            params_for_log = (
                redact_for_logging(
                    cast(RedactableDict, serializable_params),
                    sensitive_set,
                )
                if sensitive_set
                else serializable_params
            )

            # Check if structured logging is enabled
            has_structured = any(
                isinstance(h, logging.FileHandler) for h in logging.getLogger().handlers
            )

            # Log function call
            if has_structured:
                structlogger = structlog.get_logger(module_name)
                structlogger.debug(
                    "Calling function",
                    function=func_name,
                    parameters=params_for_log,
                    module=module_name,
                    lineno=line_no,
                )

            func_logger.debug(
                "%s(%s)", func_name, json.dumps(params_for_log, default=str)
            )

            return (
                func_logger,
                has_structured,
                time.time(),
                func_name,
                module_name,
                line_no,
            )

        def _log_call_success(
            result: Any,
            start_time: float,
            sensitive_set: set[str],
            func_logger: logging.Logger,
            has_structured: bool,
            func_name: str,
            module_name: str,
            line_no: int,
        ) -> None:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            # Prepare result for logging
            result_for_log: Any
            serializable_result: Any
            if isinstance(result, (list, dict)) and len(str(result)) > 1000:
                result_for_log = (
                    f"<Large result of type {type(result).__name__}, "
                    f"length: {len(str(result))}>"
                )
                serializable_result = result_for_log
            else:
                result_for_log = result
                # Make result JSON serializable for structured logging
                try:
                    json.dumps(result)  # Test if result is JSON serializable
                    serializable_result = result
                except (TypeError, OverflowError):
                    serializable_result = str(result) if result is not None else None

            # Apply redaction to result if it's a dict
            if sensitive_set and isinstance(serializable_result, dict):
                serializable_result = redact_for_logging(
                    serializable_result, sensitive_set
                )
            if sensitive_set and isinstance(result_for_log, dict):
                result_for_log = redact_for_logging(result_for_log, sensitive_set)

            # Log completion
            if has_structured:
                structlogger = structlog.get_logger(module_name)
                structlogger.debug(
                    "Function completed",
                    function=func_name,
                    execution_time_ms=elapsed_ms,
                    status="success",
                    result=serializable_result,
                    module=module_name,
                    lineno=line_no,
                )

            func_logger.debug("%s -> %s (%sms)", func_name, result_for_log, elapsed_ms)

        def _log_call_error(
            error: Exception,
            start_time: float,
            func_logger: logging.Logger,
            has_structured: bool,
            func_name: str,
            module_name: str,
            line_no: int,
        ) -> None:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            if has_structured:
                structlogger = structlog.get_logger(module_name)
                structlogger.error(
                    "Function failed",
                    function=func_name,
                    execution_time_ms=elapsed_ms,
                    error_type=type(error).__name__,
                    error_message=str(error),
                    module=module_name,
                    lineno=line_no,
                    exc_info=True,
                )

            func_logger.error(
                "%s FAILED: %s: %s (%sms)",
                func_name,
                type(error).__name__,
                str(error),
                elapsed_ms,
                exc_info=True,
            )

        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            func_logger, has_structured, start_time, func_name, module_name, line_no = (
                _log_call_start(fn, args, kwargs, sensitive_set)
            )
            try:
                result = fn(*args, **kwargs)
                _log_call_success(
                    result,
                    start_time,
                    sensitive_set,
                    func_logger,
                    has_structured,
                    func_name,
                    module_name,
                    line_no,
                )
                return result
            except Exception as e:
                _log_call_error(
                    e,
                    start_time,
                    func_logger,
                    has_structured,
                    func_name,
                    module_name,
                    line_no,
                )
                raise

        @wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            func_logger, has_structured, start_time, func_name, module_name, line_no = (
                _log_call_start(fn, args, kwargs, sensitive_set)
            )
            try:
                result = await fn(*args, **kwargs)  # type: ignore[misc]
                _log_call_success(
                    result,
                    start_time,
                    sensitive_set,
                    func_logger,
                    has_structured,
                    func_name,
                    module_name,
                    line_no,
                )
                return result  # type: ignore[no-any-return]
            except Exception as e:
                _log_call_error(
                    e,
                    start_time,
                    func_logger,
                    has_structured,
                    func_name,
                    module_name,
                    line_no,
                )
                raise

        if asyncio.iscoroutinefunction(fn):
            return cast(Callable[..., T], async_wrapper)
        return cast(Callable[..., T], wrapper)

    # Handle both @log_function_call and @log_function_call(sensitive_fields=[...])
    if func is not None:
        # Called without parentheses: @log_function_call
        return decorator(func)
    # Called with parentheses: @log_function_call(sensitive_fields=[...])
    return decorator

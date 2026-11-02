import io
import logging
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

import mcp_coder_utils.log_utils as log_utils_module
from mcp_coder_utils.log_utils import (
    _HANDLER_MARKER,
    OUTPUT,
    STANDARD_LOG_FIELDS,
    CleanFormatter,
    ExtraFieldsFormatter,
    _parse_level,
    setup_logging,
)


@pytest.fixture
def clean_root_logger() -> Iterator[Callable[[], logging.Logger]]:
    """Yield a callable returning the root logger stripped of its handlers.

    Call it as the first statement of the test: pytest's logging plugin
    re-attaches its capture handlers to the root logger *after* fixture setup,
    so the handlers can only be stripped from inside the test body.

    Teardown always runs, whether or not the test called the fixture: the
    handlers the test itself added are closed and removed, then the original
    handlers (e.g. pytest's capture handlers) and level are restored. Handlers
    captured at fixture setup or by ``_clean`` are only detached, never closed:
    pytest owns those instances and reuses them for the rest of the session.
    """
    root_logger = logging.getLogger()
    initial_handlers: list[logging.Handler] = root_logger.handlers[:]
    initial_level: int = root_logger.level

    def _clean() -> logging.Logger:
        nonlocal initial_handlers, initial_level
        initial_handlers = root_logger.handlers[:]
        initial_level = root_logger.level
        for handler in initial_handlers:
            root_logger.removeHandler(handler)
        return root_logger

    try:
        yield _clean
    finally:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            if not any(handler is original for original in initial_handlers):
                handler.close()
        for handler in initial_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(initial_level)


class TestOutputLevel:
    """Tests for the custom OUTPUT log level."""

    def test_output_level_is_registered(self) -> None:
        """Test that OUTPUT level name is registered with logging."""
        assert logging.getLevelName(25) == "OUTPUT"

    def test_output_level_value(self) -> None:
        """Test that OUTPUT constant has the expected value."""
        assert OUTPUT == 25

    def test_output_between_info_and_warning(self) -> None:
        """Test that OUTPUT sits between INFO and WARNING."""
        assert logging.INFO < OUTPUT < logging.WARNING

    def test_setup_logging_accepts_output(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """Test that setup_logging works with OUTPUT level."""
        root_logger = clean_root_logger()

        setup_logging("OUTPUT")

        assert root_logger.level == 25


class TestParseLevel:
    """Tests for the _parse_level helper."""

    def test_parse_string_level(self) -> None:
        """Standard string level names resolve to their numeric value."""
        assert _parse_level("INFO") == logging.INFO

    def test_parse_custom_string_level_case_insensitive(self) -> None:
        """Custom level names resolve case-insensitively via getLevelName."""
        assert _parse_level("output") == OUTPUT

    def test_parse_int_passthrough(self) -> None:
        """Integer levels are returned unchanged."""
        assert _parse_level(logging.DEBUG) == logging.DEBUG

    def test_parse_output_constant_passthrough(self) -> None:
        """The exported OUTPUT int constant passes through unchanged."""
        assert _parse_level(OUTPUT) == OUTPUT

    def test_parse_invalid_string_raises(self) -> None:
        """An unknown string level raises ValueError."""
        with pytest.raises(ValueError):
            _parse_level("NOPE")


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def test_setup_logging_console_only(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """Test that console logging is configured correctly."""
        root_logger = clean_root_logger()

        # Execute
        setup_logging("INFO")

        # Verify
        handlers = root_logger.handlers
        assert len(handlers) == 1
        assert isinstance(handlers[0], logging.StreamHandler)
        assert root_logger.level == logging.INFO

    def test_setup_logging_with_file(
        self, clean_root_logger: Callable[[], logging.Logger], tmp_path: Path
    ) -> None:
        """Test that file logging is configured correctly."""
        # Setup - use pytest's tmp_path for automatic cleanup
        root_logger = clean_root_logger()
        log_file = tmp_path / "logs" / "test.log"

        # Execute
        setup_logging("DEBUG", str(log_file))

        # Verify
        handlers = root_logger.handlers
        # In testing environment, we may have additional handlers from pytest
        # so we check that at least one file handler was added
        file_handlers: list[logging.FileHandler] = [
            h for h in handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) >= 1, "At least one file handler should be added"
        assert root_logger.level == logging.DEBUG

        # Verify log directory was created
        assert log_file.parent.exists()

        # Verify our specific file handler exists with correct path
        our_file_handler: logging.FileHandler | None = None
        for handler in file_handlers:
            if isinstance(handler, logging.FileHandler) and handler.baseFilename == str(
                log_file.absolute()
            ):
                our_file_handler = handler
                break

        assert our_file_handler is not None, "Our specific file handler should exist"

    def test_invalid_log_level(self) -> None:
        """Test that an invalid log level raises a ValueError."""
        with pytest.raises(ValueError):
            setup_logging("INVALID_LEVEL")

    def test_invalid_log_level_keeps_existing_handlers(
        self, clean_root_logger: Callable[[], logging.Logger], tmp_path: Path
    ) -> None:
        """A failed call with a bad log_level leaves the working setup intact."""
        root_logger = clean_root_logger()
        log_file = tmp_path / "logs" / "test.log"
        setup_logging("DEBUG", str(log_file))
        handlers_before = root_logger.handlers[:]
        level_before = root_logger.level
        assert handlers_before, "precondition: a handler must be installed"

        with pytest.raises(ValueError):
            setup_logging("INVALID_LEVEL")

        # Handlers were neither removed nor closed, and the level is unchanged.
        assert root_logger.handlers == handlers_before
        assert root_logger.level == level_before

        # The surviving file handler is still usable.
        logging.getLogger("invalid_level_probe").debug("survives bad level")
        for handler in root_logger.handlers:
            handler.flush()
        assert "survives bad level" in log_file.read_text(encoding="utf-8")

    def test_invalid_console_level_keeps_existing_handlers(
        self, clean_root_logger: Callable[[], logging.Logger], tmp_path: Path
    ) -> None:
        """A failed call with a bad console_level leaves the working setup intact."""
        root_logger = clean_root_logger()
        log_file = tmp_path / "logs" / "test.log"
        setup_logging("DEBUG", str(log_file))
        handlers_before = root_logger.handlers[:]
        level_before = root_logger.level
        assert handlers_before, "precondition: a handler must be installed"

        with pytest.raises(ValueError):
            setup_logging("DEBUG", str(log_file), console_level="INVALID_LEVEL")

        assert root_logger.handlers == handlers_before
        assert root_logger.level == level_before

        logging.getLogger("invalid_console_level_probe").debug(
            "survives bad console level"
        )
        for handler in root_logger.handlers:
            handler.flush()
        assert "survives bad console level" in log_file.read_text(encoding="utf-8")


class TestSetupLoggingIdempotency:
    """Tests for marker-based idempotent handler management."""

    def test_repeated_console_calls_single_marked_handler(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """Two console-mode calls leave exactly one marked console handler."""
        root_logger = clean_root_logger()

        setup_logging("INFO")
        setup_logging("INFO")

        marked = [h for h in root_logger.handlers if getattr(h, _HANDLER_MARKER, False)]
        assert len(marked) == 1
        assert isinstance(marked[0], logging.StreamHandler)

    def test_foreign_handler_survives(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """A pre-attached unmarked handler survives; ours is still added."""
        root_logger = clean_root_logger()
        foreign_handler = logging.StreamHandler()
        root_logger.addHandler(foreign_handler)

        setup_logging("INFO")

        # Foreign handler untouched.
        assert foreign_handler in root_logger.handlers
        assert not getattr(foreign_handler, _HANDLER_MARKER, False)

        # Our marked handler added alongside it.
        marked = [h for h in root_logger.handlers if getattr(h, _HANDLER_MARKER, False)]
        assert len(marked) == 1
        assert marked[0] is not foreign_handler

    def test_repeated_file_calls_single_marked_file_handler(
        self, clean_root_logger: Callable[[], logging.Logger], tmp_path: Path
    ) -> None:
        """Repeated file-mode calls to the same path do not accumulate handlers."""
        root_logger = clean_root_logger()
        log_file = tmp_path / "logs" / "test.log"

        setup_logging("DEBUG", str(log_file))
        setup_logging("DEBUG", str(log_file))
        setup_logging("DEBUG", str(log_file))

        marked_file_handlers = [
            h
            for h in root_logger.handlers
            if getattr(h, _HANDLER_MARKER, False) and isinstance(h, logging.FileHandler)
        ]
        assert len(marked_file_handlers) == 1


class TestSetupLoggingFormatterSelection:
    """Tests for formatter selection based on threshold."""

    def _get_console_formatter(
        self, root_logger: logging.Logger, log_level: str
    ) -> logging.Formatter:
        """Helper to get the console formatter after setup_logging."""
        setup_logging(log_level)

        stream_handlers = [
            h
            for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(stream_handlers) == 1
        formatter = stream_handlers[0].formatter
        assert formatter is not None
        return formatter

    def test_output_threshold_uses_clean_formatter(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """OUTPUT threshold should use CleanFormatter."""
        formatter = self._get_console_formatter(clean_root_logger(), "OUTPUT")
        assert isinstance(formatter, CleanFormatter)

    def test_info_threshold_uses_extra_fields_formatter(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """INFO threshold should use ExtraFieldsFormatter."""
        formatter = self._get_console_formatter(clean_root_logger(), "INFO")
        assert isinstance(formatter, ExtraFieldsFormatter)

    def test_debug_threshold_uses_extra_fields_formatter(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """DEBUG threshold should use ExtraFieldsFormatter."""
        formatter = self._get_console_formatter(clean_root_logger(), "DEBUG")
        assert isinstance(formatter, ExtraFieldsFormatter)


class TestSetupLoggingDualMode:
    """Tests for the console_level parameter and simultaneous file+console sinks."""

    def _marked_handlers(self) -> list[logging.Handler]:
        """Return the handlers setup_logging tagged on the root logger."""
        root_logger = logging.getLogger()
        return [h for h in root_logger.handlers if getattr(h, _HANDLER_MARKER, False)]

    def test_root_floor_is_min_of_levels(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """log_level=INFO, console_level=DEBUG -> root floor lowered to DEBUG.

        Proves DEBUG records are not pre-filtered at the logger. This is the
        case the motivating INFO/OUTPUT scenario would miss.
        """
        root_logger = clean_root_logger()

        setup_logging("INFO", console_level="DEBUG")

        assert root_logger.level == logging.DEBUG

    def test_dual_sinks_structure(
        self, clean_root_logger: Callable[[], logging.Logger], tmp_path: Path
    ) -> None:
        """File + console_level=OUTPUT -> one file handler at INFO, one console at OUTPUT."""
        root_logger = clean_root_logger()
        log_file = tmp_path / "logs" / "test.log"

        setup_logging("INFO", str(log_file), console_level=OUTPUT)

        marked = self._marked_handlers()
        file_handlers = [h for h in marked if isinstance(h, logging.FileHandler)]
        console_handlers = [
            h
            for h in marked
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]

        assert len(file_handlers) == 1
        assert file_handlers[0].level == logging.INFO

        assert len(console_handlers) == 1
        assert console_handlers[0].level == OUTPUT
        assert isinstance(console_handlers[0].formatter, CleanFormatter)

        # min(20, 25) == 20
        assert root_logger.level == logging.INFO

    def test_dual_mode_behavioural_file_gets_record_console_filters(
        self, clean_root_logger: Callable[[], logging.Logger], tmp_path: Path
    ) -> None:
        """An INFO record lands in the file but is filtered from the OUTPUT console."""
        root_logger = clean_root_logger()
        log_file = tmp_path / "logs" / "test.log"

        setup_logging("INFO", str(log_file), console_level=OUTPUT)

        # Redirect the marked console handler's stream to a StringIO so we can
        # capture what the console handler actually emits.
        console_handlers = [
            h
            for h in self._marked_handlers()
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 1
        captured = io.StringIO()
        console_handlers[0].setStream(captured)

        logging.getLogger("dual_mode_x").info("trail line")

        # Flush + close file handlers so the record is on disk.
        for handler in self._marked_handlers():
            handler.flush()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)

        file_contents = log_file.read_text(encoding="utf-8")
        assert "trail line" in file_contents

        console_output = captured.getvalue()
        assert "trail line" not in console_output

    def test_console_formatter_from_console_level(
        self, clean_root_logger: Callable[[], logging.Logger], tmp_path: Path
    ) -> None:
        """File + console_level=DEBUG -> console handler uses ExtraFieldsFormatter."""
        clean_root_logger()
        log_file = tmp_path / "logs" / "test.log"

        setup_logging("INFO", str(log_file), console_level="DEBUG")

        console_handlers = [
            h
            for h in self._marked_handlers()
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_handlers) == 1
        assert isinstance(console_handlers[0].formatter, ExtraFieldsFormatter)

    def test_console_level_without_log_file(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """console_level without log_file -> console only, root floor at DEBUG."""
        root_logger = clean_root_logger()

        setup_logging("DEBUG", console_level=OUTPUT)

        marked = self._marked_handlers()
        file_handlers = [h for h in marked if isinstance(h, logging.FileHandler)]
        console_handlers = [
            h
            for h in marked
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]

        assert len(file_handlers) == 0
        assert len(console_handlers) == 1
        assert console_handlers[0].level == OUTPUT
        assert root_logger.level == logging.DEBUG

    def test_backwards_compat_console_only(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """setup_logging(INFO) with no console_level -> console only, no file."""
        root_logger = clean_root_logger()

        setup_logging("INFO")

        marked = self._marked_handlers()
        file_handlers = [h for h in marked if isinstance(h, logging.FileHandler)]
        console_handlers = [
            h
            for h in marked
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]

        assert len(file_handlers) == 0
        assert len(console_handlers) == 1
        assert root_logger.level == logging.INFO

    def test_backwards_compat_file_only(
        self, clean_root_logger: Callable[[], logging.Logger], tmp_path: Path
    ) -> None:
        """setup_logging(INFO, log_file) with no console_level -> file only."""
        root_logger = clean_root_logger()
        log_file = tmp_path / "logs" / "test.log"

        setup_logging("INFO", str(log_file))

        marked = self._marked_handlers()
        file_handlers = [h for h in marked if isinstance(h, logging.FileHandler)]
        console_handlers = [
            h
            for h in marked
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]

        assert len(file_handlers) == 1
        assert len(console_handlers) == 0
        assert root_logger.level == logging.INFO

    def test_empty_log_file_falls_back_to_console(
        self, clean_root_logger: Callable[[], logging.Logger]
    ) -> None:
        """setup_logging(INFO, "") -> console only, never a sinkless config."""
        root_logger = clean_root_logger()

        setup_logging("INFO", "")

        marked = self._marked_handlers()
        file_handlers = [h for h in marked if isinstance(h, logging.FileHandler)]
        console_handlers = [
            h
            for h in marked
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]

        assert len(file_handlers) == 0
        assert len(console_handlers) == 1
        assert console_handlers[0].level == logging.INFO
        assert root_logger.level == logging.INFO

    def test_console_level_accepts_string_and_int(
        self, clean_root_logger: Callable[[], logging.Logger], tmp_path: Path
    ) -> None:
        """console_level accepts both a string name and the OUTPUT int constant."""
        clean_root_logger()
        log_file = tmp_path / "logs" / "test.log"

        setup_logging("INFO", str(log_file), console_level="OUTPUT")
        console_str = [
            h
            for h in self._marked_handlers()
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_str) == 1
        assert console_str[0].level == OUTPUT

        setup_logging("INFO", str(log_file), console_level=OUTPUT)
        console_int = [
            h
            for h in self._marked_handlers()
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.FileHandler)
        ]
        assert len(console_int) == 1
        assert console_int[0].level == OUTPUT


class TestPublicExports:
    """Tests for the module's public export contract (__all__)."""

    def test_formatter_symbols_in_all(self) -> None:
        """CleanFormatter, ExtraFieldsFormatter, STANDARD_LOG_FIELDS are exported."""
        assert "CleanFormatter" in log_utils_module.__all__
        assert "ExtraFieldsFormatter" in log_utils_module.__all__
        assert "STANDARD_LOG_FIELDS" in log_utils_module.__all__

    def test_formatter_symbols_importable(self) -> None:
        """The exported formatter symbols resolve to non-None objects."""
        assert CleanFormatter is not None
        assert ExtraFieldsFormatter is not None
        assert STANDARD_LOG_FIELDS is not None

    def test_all_names_are_real_attributes(self) -> None:
        """Every name listed in __all__ resolves to a real module attribute."""
        for name in log_utils_module.__all__:
            assert hasattr(log_utils_module, name), f"{name} missing from module"

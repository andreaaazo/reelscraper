import logging
import unittest
from typing import List
from unittest.mock import patch, MagicMock
from logging.handlers import RotatingFileHandler

from reelscraper.utils.logger_manager import LoggerManager


class ListHandler(logging.Handler):
    """
    A custom logging handler that stores log records in a list.
    """

    def __init__(self):
        super().__init__()
        self.records: List[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class TestLoggerManager(unittest.TestCase):
    def setUp(self):
        # Create a ListHandler to capture log records.
        self.list_handler = ListHandler()

        # Create a LoggerManager instance with a custom name to avoid clashing with other tests.
        self.logger_manager = LoggerManager(name="TestLogger", level=logging.DEBUG)
        # Remove any previously configured handlers.
        self.logger_manager.logger.handlers = []
        # Add our list handler.
        self.logger_manager.logger.addHandler(self.list_handler)
        # Also, set the logger level appropriately.
        self.logger_manager.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        # Remove handlers after each test.
        self.logger_manager.logger.removeHandler(self.list_handler)
        self.list_handler.records.clear()

    def test_log_account_error(self):
        account = "test_account"
        self.logger_manager.log_account_error(account)
        self.assertEqual(len(self.list_handler.records), 1)
        record = self.list_handler.records[0]
        self.assertEqual(record.levelno, logging.ERROR)
        expected_message = f"Account: {account} | Failed to fetch reels after retries"
        self.assertIn(expected_message, record.getMessage())

    def test_log_retry(self):
        account = "retry_account"
        retry, max_retries = 2, 5
        self.logger_manager.log_retry(retry, max_retries, account)
        self.assertEqual(len(self.list_handler.records), 1)
        record = self.list_handler.records[0]
        self.assertEqual(record.levelno, logging.WARNING)
        expected_message = f"Account: {account} | Retry {retry}/{max_retries}"
        self.assertIn(expected_message, record.getMessage())

    def test_log_account_success(self):
        account = "success_account"
        reel_count = 3
        self.logger_manager.log_account_success(account, reel_count)
        self.assertEqual(len(self.list_handler.records), 1)
        record = self.list_handler.records[0]
        self.assertEqual(record.levelno, logging.INFO)
        expected_message = f"SUCCESS | {reel_count} Reels of {account}"
        self.assertIn(expected_message, record.getMessage())

    def test_log_account_begin(self):
        account = "begin_account"
        self.logger_manager.log_account_begin(account)
        self.assertEqual(len(self.list_handler.records), 1)
        record = self.list_handler.records[0]
        self.assertEqual(record.levelno, logging.INFO)
        expected_message = f"Account: {account} | Begin scraping..."
        self.assertIn(expected_message, record.getMessage())

    @patch("reelscraper.utils.logger_manager.os.path.exists", return_value=False)
    @patch("reelscraper.utils.logger_manager.os.makedirs")
    @patch(
        "reelscraper.utils.logger_manager.os.path.join",
        side_effect=lambda log_dir, filename: f"{log_dir}/{filename}",
    )
    def test_save_log_creates_file_handler(
        self, mock_path_join, mock_makedirs, mock_exists
    ):
        """
        Test that when save_log is True a file handler is added by calling _configure_file_handler.
        This test patches os.makedirs, os.path.join, and the internal _configure_file_handler method.
        """
        level = logging.DEBUG
        max_bytes = 1024
        backup_count = 3
        fmt = "%(asctime)s - %(levelname)s - %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"

        with patch.object(LoggerManager, "_configure_file_handler") as mock_configure:
            logger_name = "TestLoggerSave"
            logger_manager = LoggerManager(
                name=logger_name,
                level=level,
                save_log=True,
                max_bytes=max_bytes,
                backup_count=backup_count,
                fmt=fmt,
                datefmt=datefmt,
            )
            # Verify that os.makedirs was called to create the "logs" directory.
            mock_makedirs.assert_called_with("logs", exist_ok=True)

            # Check the log file path that should be used.
            expected_log_file = f"logs/{logger_name}.log"
            mock_path_join.assert_called_with("logs", f"{logger_name}.log")

            # Verify that _configure_file_handler was called with the expected arguments.
            mock_configure.assert_called_with(
                log_level=level,
                formatter=logger_manager.logger.handlers[0].formatter,
                filename=expected_log_file,
                max_bytes=max_bytes,
                backup_count=backup_count,
            )

    @patch("reelscraper.utils.logger_manager.os.path.exists", return_value=False)
    @patch("reelscraper.utils.logger_manager.os.makedirs")
    @patch(
        "reelscraper.utils.logger_manager.os.path.join",
        side_effect=lambda log_dir, filename: f"{log_dir}/{filename}",
    )
    def test_file_handler_setup(self, mock_path_join, mock_makedirs, mock_exists):
        """
        This test verifies that when save_log is True the following lines are executed:

            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{name}.log")
            self._configure_file_handler(...)
        """
        logger_name = "TestLoggerFile"
        level = logging.DEBUG
        max_bytes = 2048
        backup_count = 5
        fmt = "%(asctime)s - %(levelname)s - %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"

        with patch.object(LoggerManager, "_configure_file_handler") as mock_configure:
            logger_manager = LoggerManager(
                name=logger_name,
                level=level,
                save_log=True,
                max_bytes=max_bytes,
                backup_count=backup_count,
                fmt=fmt,
                datefmt=datefmt,
            )
            mock_makedirs.assert_called_with("logs", exist_ok=True)

            expected_log_file = f"logs/{logger_name}.log"
            mock_path_join.assert_called_with("logs", f"{logger_name}.log")

            mock_configure.assert_called_with(
                log_level=level,
                formatter=unittest.mock.ANY,
                filename=expected_log_file,
                max_bytes=max_bytes,
                backup_count=backup_count,
            )

    @patch("reelscraper.utils.logger_manager.RotatingFileHandler", autospec=True)
    def test_rotating_file_handler_creation(self, mock_rotating_handler):
        """
        Test that RotatingFileHandler is created correctly and attached to the logger.
        """
        filename = "logs/TestLogger.log"
        level = logging.DEBUG
        max_bytes = 2048
        backup_count = 5
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # We'll use the same LoggerManager from setUp, since we only test _configure_file_handler here.
        lm = self.logger_manager

        # Mock the actual RotatingFileHandler.
        dummy_handler = MagicMock(spec=RotatingFileHandler)
        mock_rotating_handler.return_value = dummy_handler

        # Call the method under test.
        lm._configure_file_handler(
            log_level=level,
            formatter=formatter,
            filename=filename,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )

        # Verify correct instantiation.
        mock_rotating_handler.assert_called_with(
            filename=filename, maxBytes=max_bytes, backupCount=backup_count
        )
        # Verify level and formatter.
        dummy_handler.setLevel.assert_called_once_with(level)
        dummy_handler.setFormatter.assert_called_once_with(formatter)
        # Verify it was attached to the logger.
        self.assertIn(dummy_handler, lm.logger.handlers)

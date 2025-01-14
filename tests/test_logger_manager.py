import logging
import unittest
from typing import List
from unittest.mock import patch, ANY, MagicMock
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

        # Create a LoggerManager instance with a custom logger name to avoid clashing with other tests.
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

        # There should be one log record.
        self.assertEqual(len(self.list_handler.records), 1)
        record = self.list_handler.records[0]
        self.assertEqual(record.levelno, logging.ERROR)
        expected_message = f"Account: {account} | Failed to fetch reels after retries"
        self.assertIn(expected_message, record.getMessage())

    def test_log_retry(self):
        account = "retry_account"
        retry, max_retries = 2, 5
        self.logger_manager.log_retry(retry, max_retries, account)

        # There should be one log record.
        self.assertEqual(len(self.list_handler.records), 1)
        record = self.list_handler.records[0]
        self.assertEqual(record.levelno, logging.WARNING)
        expected_message = f"Account: {account} | Retry {retry}/{max_retries}"
        self.assertIn(expected_message, record.getMessage())

    def test_log_account_success(self):
        account = "success_account"
        reel_count = 3
        self.logger_manager.log_account_success(account, reel_count)

        # There should be one log record.
        self.assertEqual(len(self.list_handler.records), 1)
        record = self.list_handler.records[0]
        self.assertEqual(record.levelno, logging.INFO)
        expected_message = f"SUCCESS | {reel_count} Reels of {account}"
        self.assertIn(expected_message, record.getMessage())

    def test_log_account_begin(self):
        account = "begin_account"
        self.logger_manager.log_account_begin(account)

        # There should be one log record.
        self.assertEqual(len(self.list_handler.records), 1)
        record = self.list_handler.records[0]
        self.assertEqual(record.levelno, logging.INFO)
        expected_message = f"Account: {account} | Begin scraping..."
        self.assertIn(expected_message, record.getMessage())

    @patch("os.makedirs")
    @patch(
        "os.path.join", side_effect=lambda log_dir, filename: f"{log_dir}/{filename}"
    )
    def test_save_log_creates_file_handler(self, mock_path_join, mock_makedirs):
        """
        Test that when save_log is True a file handler is added by calling _add_file_handler.
        This test patches os.makedirs, os.path.join, and the internal _add_file_handler method.
        """
        # Define parameters for creating the logger.
        level = logging.DEBUG
        max_bytes = 1024
        backup_count = 3

        # Instead of passing a Formatter instance, we pass the format string and date format.
        fmt = "%(asctime)s - %(levelname)s - %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"

        # Patch _add_file_handler to spy on its call.
        with patch.object(LoggerManager, "_add_file_handler") as mock_add_file_handler:
            # Initialize LoggerManager with save_log True.
            logger_name = "TestLoggerSave"
            logger_manager = LoggerManager(
                name=logger_name,
                level=level,
                save_log=True,
                max_bytes=max_bytes,
                backup_count=backup_count,
                fmt=fmt,  # Pass format string instead of a Formatter
                datefmt=datefmt,  # Pass the date format if required by your LoggerManager
            )

            # Verify that os.makedirs was called to create the "logs" directory.
            mock_makedirs.assert_called_with("logs", exist_ok=True)

            # Check the log file path that should be used.
            expected_log_file = f"logs/{logger_name}.log"
            mock_path_join.assert_called_with("logs", f"{logger_name}.log")

            # Verify that _add_file_handler was called with the expected arguments.
            mock_add_file_handler.assert_called_with(
                level=level,
                formatter=ANY,  # We allow any Formatter instance
                filename=expected_log_file,
                max_bytes=max_bytes,
                backup_count=backup_count,
            )

    @patch("os.makedirs")
    @patch(
        "os.path.join", side_effect=lambda log_dir, filename: f"{log_dir}/{filename}"
    )
    def test_file_handler_setup(self, mock_path_join, mock_makedirs):
        """
        This test verifies that when save_log is True the following lines are executed:

            log_dir: str = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file: str = os.path.join(log_dir, f"{name}.log")
            self._add_file_handler(...)

        We verify this by patching os.makedirs, os.path.join, and _add_file_handler.
        """
        # Define expected parameters.
        logger_name = "TestLoggerFile"
        level = logging.DEBUG
        max_bytes = 2048
        backup_count = 5

        # Instead of passing a Formatter, pass the format string that LoggerManager expects.
        fmt = "%(asctime)s - %(levelname)s - %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"

        # Patch _add_file_handler to capture its call.
        with patch.object(LoggerManager, "_add_file_handler") as mock_add_file_handler:
            # Initialize the LoggerManager with save_log enabled so that the branch is taken.
            logger_manager = LoggerManager(
                name=logger_name,
                level=level,
                save_log=True,
                max_bytes=max_bytes,
                backup_count=backup_count,
                fmt=fmt,  # Pass the format string expected by LoggerManager
                datefmt=datefmt,  # Pass the date format if needed by LoggerManager
            )

            # Assert that os.makedirs was called with the "logs" directory.
            mock_makedirs.assert_called_with("logs", exist_ok=True)

            # Verify that os.path.join was used correctly.
            expected_log_file = f"logs/{logger_name}.log"
            mock_path_join.assert_called_with("logs", f"{logger_name}.log")

            # Finally, verify that _add_file_handler was called with the correct arguments.
            mock_add_file_handler.assert_called_with(
                level=level,
                # LoggerManager should internally create the Formatter using the provided fmt/datefmt.
                formatter=unittest.mock.ANY,  # We use ANY if we don't need to assert specifics on the Formatter
                filename=expected_log_file,
                max_bytes=max_bytes,
                backup_count=backup_count,
            )

    @patch("reelscraper.utils.logger_manager.RotatingFileHandler", autospec=True)
    def test_rotating_file_handler_creation(self, mock_rotating_handler):
        """
        Test that RotatingFileHandler is created correctly and attached to the logger.
        The code under test is:
            file_handler: RotatingFileHandler = RotatingFileHandler(
                filename=filename, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        """
        # Define expected parameters.
        filename = "logs/TestLogger.log"
        level = logging.DEBUG
        max_bytes = 2048
        backup_count = 5

        # Create a formatter instance.
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        # Create an instance of LoggerManager (it doesn't matter whether save_log is True or not)
        # because we are directly testing the _add_file_handler method.
        lm = self.logger_manager

        # Prepare a dummy RotatingFileHandler instance.
        dummy_handler = MagicMock(spec=RotatingFileHandler)
        mock_rotating_handler.return_value = dummy_handler

        # Call the method under test.
        lm._add_file_handler(
            level=level,
            formatter=formatter,
            filename=filename,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )

        # Verify that RotatingFileHandler was instantiated with the correct arguments.
        mock_rotating_handler.assert_called_with(
            filename=filename, maxBytes=max_bytes, backupCount=backup_count
        )

        # Verify that the file handler's level was set correctly.
        dummy_handler.setLevel.assert_called_once_with(level)

        # Verify that the file handler's formatter was set correctly.
        dummy_handler.setFormatter.assert_called_once_with(formatter)

        # Verify that the new file handler was added to the logger.
        self.assertIn(dummy_handler, lm.logger.handlers)


if __name__ == "__main__":
    unittest.main()

import logging
import unittest
from typing import List

from reelscraper.utils.logging import LoggerManager


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
        expected_message = f"Account: {account} | Reels: {reel_count}"
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


if __name__ == "__main__":
    unittest.main()

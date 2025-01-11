import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


class LoggerManager:
    def __init__(
        self,
        name: str = __name__,
        level: int = logging.INFO,
        fmt: str = "[%(levelname)s] %(asctime)s | %(name)s | %(message)s",
        datefmt: str = "%H:%M:%S",
        log_file: Optional[str] = None,
        max_bytes: int = 1_000_000,
        backup_count: int = 3,
    ):
        """
        Initializes and configures a logger.

        :param name: Name of the logger (usually __name__ for module logging)
        :param level: Logging level (e.g. logging.DEBUG, logging.INFO, etc.)
        :param fmt: Log message format
        :param datefmt: Date format for log messages
        :param log_file: Path to the log file (if None, file logging is disabled)
        :param max_bytes: Maximum file size in bytes before rotating the log file
        :param backup_count: Number of backup files to keep when rotating the log file
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent adding handlers multiple times if they already exist
        if not self.logger.handlers:
            formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

            # Configure console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # Configure file handler if log_file is specified
            if log_file:
                file_handler = RotatingFileHandler(
                    filename=log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

    def log_account_error(self, account_name: str):
        """
        Logs an error message for a specific account.

        :param account_name: Identifier for the account
        """
        self.logger.error(
            f"Account: {account_name} | Failed to fetch reels after retries"
        )

    def log_retry(self, retry: int, max_retries: int, account_name: str):
        """
        Logs a retry warning message, indicating the retry number for a specific account.

        :param retry: The current retry number
        :param max_retries: The maximum number of retry allowed
        :param account_name: Identifier for the account
        """
        self.logger.warning(f"RETRY {retry}/{max_retries} | Account: {account_name}")

    def log_account_success(self, username: str, reel_count: int):
        """
        Logs an info message indicating the successful processing of an account.

        :param account_name: Identifier for the account
        :param reel_count: Count of reels processed for the account
        """
        self.logger.info(f"Account: {username} | Reels: {reel_count}")

    def log_account_begin(self, username: str):
        """
        Logs an info message indicating the beginning of an account.

        :param username: Identifier for the username
        """
        self.logger.info(f"Account: {username} | Begin scraping...")

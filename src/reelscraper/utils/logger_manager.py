import logging
import os
from logging.handlers import RotatingFileHandler


class LoggerManager:
    """
    LoggerManager configures and manages logging operations.

    Uses composition for handler setup, ensuring single responsibility.
    """

    def __init__(
        self,
        name: str = __name__,
        level: int = logging.INFO,
        fmt: str = "[%(levelname)s] %(asctime)s | %(message)s",
        datefmt: str = "%H:%M:%S",
        max_bytes: int = 500_000,
        backup_count: int = 3,
        save_log: bool = False,
    ) -> None:
        """
        Initializes and configures a logger with console and optional file logging.

        **Parameters:**
        - `[name]`: Name of the logger (usually __name__ for module logging).
        - `[level]`: Logging level (e.g. logging.DEBUG, logging.INFO, etc.).
        - `[fmt]`: Log message format.
        - `[datefmt]`: Date format for log messages.
        - `[max_bytes]`: Maximum file size in bytes before rotating the log file.
        - `[backup_count]`: Number of backup files to keep when rotating the log file.
        - `[save_log]`: If True, creates a log directory and saves the log file inside it.
        """
        self.logger: logging.Logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Only configure if no handlers are present
        if not self.logger.hasHandlers():
            formatter: logging.Formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
            self._configure_console_handler(log_level=level, formatter=formatter)

            if save_log:
                log_dir: str = "logs"
                os.makedirs(log_dir, exist_ok=True)
                log_file: str = os.path.join(log_dir, f"{name}.log")
                self._configure_file_handler(
                    log_level=level,
                    formatter=formatter,
                    filename=log_file,
                    max_bytes=max_bytes,
                    backup_count=backup_count,
                )

    def _configure_console_handler(
        self, log_level: int, formatter: logging.Formatter
    ) -> None:
        """
        Adds a console stream handler to the logger.

        **Parameters:**
        - `[log_level]`: Logging level for the console handler.
        - `[formatter]`: Formatter to format log messages.
        """
        console_handler: logging.StreamHandler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _configure_file_handler(
        self,
        log_level: int,
        formatter: logging.Formatter,
        filename: str,
        max_bytes: int,
        backup_count: int,
    ) -> None:
        """
        Adds a rotating file handler to the logger.

        **Parameters:**
        - `[log_level]`: Logging level for the file handler.
        - `[formatter]`: Formatter to format log messages.
        - `[filename]`: Path to the log file.
        - `[max_bytes]`: Maximum file size in bytes before rotating.
        - `[backup_count]`: Number of backup files to keep.
        """
        file_handler: RotatingFileHandler = RotatingFileHandler(
            filename=filename, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log_account_error(self, account_name: str) -> None:
        """
        Logs an error message indicating failure for a specific account.

        **Parameters:**
        - `[account_name]`: Identifier for the account.
        """
        self.logger.error(
            f"Account: {account_name} | Failed to fetch reels after retries"
        )

    def log_retry(self, retry: int, max_retries: int, account_name: str) -> None:
        """
        Logs a warning message indicating the retry attempt for a specific account.

        **Parameters:**
        - `[retry]`: Current retry attempt number.
        - `[max_retries]`: Maximum allowed retries.
        - `[account_name]`: Identifier for the account.
        """
        self.logger.warning(
            f"RETRY | Account: {account_name} | Retry {retry}/{max_retries}"
        )

    def log_account_success(self, username: str, reel_count: int) -> None:
        """
        Logs an informational message indicating successful processing for an account.

        **Parameters:**
        - `[username]`: Identifier for the account.
        - `[reel_count]`: Number of reels processed.
        """
        self.logger.info(f"SUCCESS | {reel_count} Reels of {username}")

    def log_account_begin(self, username: str) -> None:
        """
        Logs an informational message indicating the beginning of account processing.

        **Parameters:**
        - `[username]`: Identifier for the account.
        """
        self.logger.info(f"BEGIN | Account: {username} | Begin scraping...")

    def log_reels_scraped(
        self,
        username: str,
        reel_count: int,
    ) -> None:
        """
        Logs an informational message indicating the number of reels scraped.

        **Parameters:**
        - `[username]`: Identifier for the account.
        - `[reel_count]`: Current number of reels scraped.
        """
        self.logger.debug(f"SCRAPING | Account: {username} | Reels: {reel_count}")

    def log_finish_multiscraping(
        self,
        reel_count: int,
        accounts_count: int,
    ) -> None:
        """
        Logs an informational message indicating the end of multiscraping.

        **Parameters:**
        - `[reel_count]`: Number of reels scraped.
        - `[accounts_count]`: Number of accounts scraped.
        """
        self.logger.info(
            f"SUCCESS | Scraped {reel_count} Reels from {accounts_count} Accounts"
        )

    def log_saving_scraping_results(self, reels_saved_count: int, account: str) -> None:
        """
        Logs an informational message indicating the saving of the scraping results.

        **Parameters:**
        - `[reels_saved_count]`: Number of reels successfully saved.
        - `[account]`: Identifier for the account.
        """
        self.logger.info(f"SAVING | {reels_saved_count} Reels from {account}")

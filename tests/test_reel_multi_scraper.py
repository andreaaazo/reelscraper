import os
import tempfile
import unittest
from typing import Dict, List

# Import the class under test.
from reelscraper import ReelMultiScraper

# -----------------------------------------------------------------------------
# Dummy implementations for testing:
# -----------------------------------------------------------------------------


class DummyReelScraper:
    """
    A dummy ReelScraper that simulates successful and failing responses.
    The behavior is determined by a mapping of username to either a list of reel dictionaries
    or an exception.
    """

    def __init__(
        self, results: Dict[str, List[Dict]], errors: Dict[str, Exception] = None
    ):
        """
        :param results: A dictionary mapping username to a list of reel dictionaries.
        :param errors: A dictionary mapping username to an Exception to raise.
        """
        self.results = results
        self.errors = errors if errors is not None else {}

    def get_user_reels(
        self, username: str, max_posts: int = None, max_retries: int = 10
    ) -> List[Dict]:
        # Simulate exception if specified for that username.
        if username in self.errors:
            raise self.errors[username]
        return self.results.get(username, [])


class DummyLoggerManager:
    """
    DummyLoggerManager captures log calls in an internal list for testing purposes.
    It implements the same interface as LoggerManager but does not output to the console.
    """

    def __init__(self):
        self.calls = []  # List to record all logging calls

    def log_account_error(self, account_name: str):
        """
        Record an error log call.
        :param account_name: Identifier for the account that encountered an error.
        """
        self.calls.append(("error", account_name))

    def log_retry(self, retry: int, max_retries: int, account_name: str):
        """
        Record a retry log call.
        :param retry: The current retry number.
        :param max_retries: The maximum number of retries allowed.
        :param account_name: Identifier for the account.
        """
        self.calls.append(("retry", retry, max_retries, account_name))

    def log_account_success(self, username: str, reel_count: int):
        """
        Record a success log call.
        :param username: Identifier for the account.
        :param reel_count: The count of reels processed for the account.
        """
        self.calls.append(("success", username, reel_count))

    def log_account_begin(self, username: str):
        """
        Record a begin log call.
        :param username: Identifier for the account.
        """
        self.calls.append(("begin", username))


# -----------------------------------------------------------------------------
# Test Suite for ReelMultiScraper
# -----------------------------------------------------------------------------


class TestReelMultiScraper(unittest.TestCase):

    def setUp(self):
        # Create a temporary accounts file with a list of usernames.
        self.temp_accounts_file = tempfile.NamedTemporaryFile("w+", delete=False)
        self.accounts = ["user1", "user2", "user3"]
        self.temp_accounts_file.write("\n".join(self.accounts))
        self.temp_accounts_file.flush()
        self.temp_accounts_file.close()
        # Create an instance of the dummy logger.
        self.dummy_logger = DummyLoggerManager()

    def tearDown(self):
        # Remove the temporary accounts file.
        os.unlink(self.temp_accounts_file.name)

    def test_scrape_accounts_all_successful(self):
        """
        Test that scraping all accounts in parallel returns the expected results when
        no scraping errors occur, and that successful log calls are recorded.
        """
        # Prepare dummy results for each account.
        dummy_results = {
            "user1": [{"reel": {"code": "a1"}}],
            "user2": [{"reel": {"code": "b1"}}, {"reel": {"code": "b2"}}],
            "user3": [],  # No reels for user3.
        }
        dummy_scraper = DummyReelScraper(results=dummy_results)
        multi_scraper = ReelMultiScraper(
            accounts_file=self.temp_accounts_file.name,
            scraper=dummy_scraper,
            logger_manager=self.dummy_logger,
            max_workers=3,
        )

        # Perform scraping.
        results = multi_scraper.scrape_accounts()

        # Verify that we have an entry for each account.
        self.assertEqual(set(results.keys()), set(self.accounts))
        # Validate that results match the expected output.
        self.assertEqual(results["user1"], dummy_results["user1"])
        self.assertEqual(results["user2"], dummy_results["user2"])
        self.assertEqual(results["user3"], dummy_results["user3"])
        # Verify that a success log was recorded for each account.
        expected_logs = [
            ("success", "user1", len(dummy_results["user1"])),
            ("success", "user2", len(dummy_results["user2"])),
            ("success", "user3", len(dummy_results["user3"])),
        ]
        for log in expected_logs:
            self.assertIn(log, self.dummy_logger.calls)

    def test_scrape_accounts_with_errors(self):
        """
        Test that when some accounts trigger scraping errors, the error is caught, the account
        is omitted from the returned results, and an error log is recorded.
        """
        # Simulate normal results for user1 and user3 while user2 triggers an exception.
        dummy_results = {
            "user1": [{"reel": {"code": "a1"}}],
            "user3": [{"reel": {"code": "c1"}}],
        }
        dummy_errors = {"user2": Exception("Scraping failed for user2")}
        dummy_scraper = DummyReelScraper(results=dummy_results, errors=dummy_errors)
        multi_scraper = ReelMultiScraper(
            accounts_file=self.temp_accounts_file.name,
            scraper=dummy_scraper,
            logger_manager=self.dummy_logger,
            max_workers=3,
        )

        results = multi_scraper.scrape_accounts()

        # Expect that only user1 and user3 are included.
        self.assertIn("user1", results)
        self.assertIn("user3", results)
        self.assertNotIn("user2", results)
        self.assertEqual(results["user1"], dummy_results["user1"])
        self.assertEqual(results["user3"], dummy_results["user3"])
        # Verify that an error log is recorded for user2.
        self.assertIn(("error", "user2"), self.dummy_logger.calls)

    def test_scrape_accounts_parallel_execution(self):
        """
        Test that reel scraping is performed in parallel. This test verifies that every
        account (from the temporary file) is processed by the scraper.
        """
        # Dummy scraper returns an empty list for each account.
        dummy_scraper = DummyReelScraper(results={acc: [] for acc in self.accounts})
        multi_scraper = ReelMultiScraper(
            accounts_file=self.temp_accounts_file.name,
            scraper=dummy_scraper,
            logger_manager=self.dummy_logger,
            max_workers=2,
        )

        results = multi_scraper.scrape_accounts()

        # Verify that a result exists for each account and is an empty list.
        self.assertEqual(set(results.keys()), set(self.accounts))
        for reels in results.values():
            self.assertEqual(reels, [])
        # Optionally, verify that a success log was recorded for each account.
        for account in self.accounts:
            self.assertIn(("success", account, 0), self.dummy_logger.calls)


if __name__ == "__main__":
    unittest.main()

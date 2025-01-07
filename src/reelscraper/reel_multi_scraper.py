import concurrent.futures
from typing import List, Dict
from reelscraper.utils.account_manager import AccountManager
from reelscraper.reel_scraper import ReelScraper


class ReelMultiScraper:
    """
    [ReelMultiScraper] retrieves reels for multiple Instagram accounts in parallel using [ReelScraper].

    :param [accounts_file]: Path to a text file containing one username per line
    :param [scraper]: Instance of [ReelScraper] used to fetch reels
    :param [max_workers]: Maximum number of threads to use for concurrent requests
    """

    def __init__(
        self,
        accounts_file: str,
        scraper: ReelScraper,
        max_workers: int = 5,
    ) -> None:
        """
        Initializes [MultiAccountScraper] by loading account names and storing references.

        :param [accounts_file]: Path to a text file containing one username per line
        :param [scraper]: Instance of [ReelScraper] used to fetch reels
        :param [max_workers]: Maximum number of threads to use for concurrent requests
        """
        self.account_manager: AccountManager = AccountManager(accounts_file)
        self.scraper: ReelScraper = scraper
        self.max_workers: int = max_workers
        self.accounts: List[str] = self.account_manager.get_accounts()

    def scrape_accounts(self) -> Dict[str, List[Dict]]:
        """
        Scrapes reels for each account in parallel and returns results in a dictionary.

        :return: Dictionary mapping each username to a list of reel information dictionaries
        """
        results: Dict[str, List[Dict]] = {}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            future_to_username = {
                executor.submit(self.scraper.get_user_reels, username): username
                for username in self.accounts
            }

            for future in concurrent.futures.as_completed(future_to_username):
                username = future_to_username[future]
                try:
                    reels = future.result()
                    results[username] = reels
                    print(f"Done with account: {username}")
                except Exception:
                    print(f"Error with account: {username}")

        return results

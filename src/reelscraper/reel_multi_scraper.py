import concurrent.futures
from typing import List, Dict, Optional, Any
from reelscraper.utils import AccountManager, DBManager
from reelscraper import ReelScraper


class ReelMultiScraper:
    """
    [ReelMultiScraper] retrieves reels for multiple Instagram accounts in parallel using [ReelScraper].

    **Parameters:**
    - `[scraper]`: Instance of [ReelScraper] for fetching reels
    - `[max_workers]`: Maximum number of threads for concurrent requests (default: 5)
    - `[db_manager]`: Optional [DBManager] for storing results
    """

    def __init__(
        self,
        scraper: ReelScraper,
        max_workers: int = 5,
        db_manager: Optional[DBManager] = None,
    ) -> None:
        """
        Initializes [ReelMultiScraper] with required references.

        **Parameters:**
        - `[scraper]`: Instance of [ReelScraper] used to fetch reels
        - `[max_workers]`: Maximum number of threads for concurrent requests
        - `[db_manager]`: Optional [DBManager] instance for storing reels data
        """
        self.scraper: ReelScraper = scraper
        self.max_workers: int = max_workers
        self.db_manager: Optional[DBManager] = db_manager

    def scrape_accounts(
        self,
        accounts_file: str,
        max_posts_per_profile: Optional[int] = None,
        max_retires_per_profile: Optional[int] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Scrapes reels for each username found in [accounts_file] in parallel.

        If [db_manager] is provided, results are stored in the database; otherwise, a list of reel info dictionaries is returned.

        **Parameters:**
        - `[accounts_file]`: Path to a file containing one username per line
        - `[max_posts_per_profile]`: Maximum number of reels to fetch for each account (optional)
        - `[max_retires_per_profile]`: Maximum number of retries when fetching reels (optional)

        **Returns:**
        - List of reel information dictionaries if `[db_manager]` is None, otherwise `None`.
        """
        account_manager: AccountManager = AccountManager(accounts_file)
        accounts: List[str] = account_manager.get_accounts()
        reels_count: int = 0

        # Store all results if no DB manager is provided
        all_results: List[Dict[str, Any]] = [] if self.db_manager is None else []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            future_to_username = {
                executor.submit(
                    self.scraper.get_user_reels,
                    username,
                    max_posts_per_profile,
                    max_retires_per_profile,
                ): username
                for username in accounts
            }

            for future in concurrent.futures.as_completed(future_to_username):
                username: str = future_to_username[future]
                try:
                    reels: List[Dict[str, Any]] = future.result()
                    if self.db_manager is not None:
                        self.db_manager.store_reels(username, reels)
                        if self.scraper.logger_manager is not None:
                            self.scraper.logger_manager.log_saving_scraping_results(
                                len(reels), username
                            )
                    else:
                        all_results.extend(reels)
                    reels_count += len(reels)
                except Exception:
                    # Optionally log exceptions or handle them as needed
                    pass

        if self.scraper.logger_manager is not None:
            self.scraper.logger_manager.log_finish_multiscraping(
                reels_count, len(accounts)
            )

        # Return accumulated results only if DB manager is not used
        return all_results if self.db_manager is None else None

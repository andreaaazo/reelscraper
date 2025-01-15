import tempfile
import os
import json
from typing import Dict, List, Optional, Any
from reelscraper.utils import InstagramAPI, Extractor, LoggerManager


class ReelScraper:
    """
    [ReelScraper] provides methods to gather Instagram Reels data using composition of [InstagramAPI] and [Extractor].

    :param [timeout]: Connection timeout in seconds
    :param [proxy]: Proxy string or None
    :param [logger_manager]: Optional [LoggerManager] for logging
    """

    def __init__(
        self,
        timeout: Optional[int] = None,
        proxy: Optional[str] = None,
        logger_manager: Optional[LoggerManager] = None,
    ) -> None:
        """
        Initializes [ReelScraper] with an [InstagramAPI] and an [Extractor].

        :param [timeout]: Connection timeout in seconds
        :param [proxy]: Proxy string or None (e.g., username:password@host:port)
        :param [logger_manager]: Optional instance of [LoggerManager]
        """
        self.api: InstagramAPI = InstagramAPI(timeout=timeout, proxy=proxy)
        self.extractor: Extractor = Extractor()
        self.logger_manager: Optional[LoggerManager] = logger_manager

    def _fetch_reels(
        self, username: str, max_id: Optional[str], max_retries: int
    ) -> Dict[str, Any]:
        """
        Retrieves first or subsequent batches of reels. Uses retry logic up to [max_retries].

        :param [username]: Instagram username
        :param [max_id]: Pagination identifier for further requests (None if fetching first batch)
        :param [max_retries]: Maximum number of allowed retries
        :return: Dictionary containing reels items and paging info
        :raises Exception: If data cannot be fetched within [max_retries] attempts
        """
        response: Optional[Dict[str, Any]] = None
        for retry in range(max_retries):
            if max_id is None:
                response = self.api.get_user_first_reels(username)
            else:
                response = self.api.get_user_paginated_reels(max_id, username)

            if response is not None:
                break

            if self.logger_manager is not None and retry > 0:
                self.logger_manager.log_retry(retry, max_retries, username)

        if response is None:
            if self.logger_manager is not None:
                self.logger_manager.log_account_error(username)
            raise Exception(
                f"Failed to fetch reels for '{username}' after {max_retries} retries."
            )

        return response

    def _extract_reel_info(self, reel: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract relevant fields from the raw reel dictionary.
        Customize this to your needs.

        :param reel: Raw reel dictionary
        :return: Cleaned-up reel info dict or None if invalid
        """
        media: Dict[str, Any] = reel.get("media", {})
        return self.extractor.extract_reel_info(media)

    def get_user_reels(
        self, username: str, max_posts: int = 50, max_retries: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Scrapes up to max_posts reels for the given username, streaming them to
        a temp file to avoid large in-memory lists. Returns a final list of reels.

        :param [username]: Instagram username
        :param [max_posts]: Maximum number of reels to fetch (default: 50)
        :param [max_retries]: Maximum number of retry attempts for each batch
        :return: List of dictionaries with reel information
        :raises Exception: If initial reels cannot be fetched for [username]
        """
        if self.logger_manager is not None:
            self.logger_manager.log_account_begin(username)

        reels_count = 0

        temp_file = tempfile.NamedTemporaryFile(
            mode="w+", suffix=".jsonl", delete=False
        )
        temp_path = temp_file.name

        try:
            # Fetch the first batch of reels
            first_reels_response: Dict[str, Any] = self._fetch_reels(
                username=username, max_id=None, max_retries=max_retries
            )
            first_reels: List[Dict[str, Any]] = first_reels_response["items"]
            paging_info: Dict[str, Any] = first_reels_response["paging_info"]

            for reel in first_reels:

                reel_info: Optional[Dict[str, Any]] = self._extract_reel_info(reel)
                if reel_info:
                    temp_file.write(json.dumps(reel_info) + "\n")
                    reels_count += 1
                if reels_count >= max_posts:
                    if self.logger_manager is not None:
                        self.logger_manager.log_account_success(username, reels_count)
                    break

            if self.logger_manager is not None:
                self.logger_manager.log_reels_scraped(username, reels_count)

            # Paginate while more reels are available
            while paging_info.get("more_available", False) and reels_count < max_posts:
                max_id: str = paging_info.get("max_id", "")
                paginated_reels_response: Dict[str, Any] = self._fetch_reels(
                    username=username, max_id=max_id, max_retries=max_retries
                )
                paginated_reels: List[Dict[str, Any]] = paginated_reels_response[
                    "items"
                ]

                for reel in paginated_reels:
                    reel_info: Optional[Dict[str, Any]] = self._extract_reel_info(reel)
                    if reel_info:
                        temp_file.write(json.dumps(reel_info) + "\n")
                        reels_count += 1
                    if reels_count >= max_posts:
                        if self.logger_manager is not None:
                            self.logger_manager.log_account_success(
                                username, reels_count
                            )
                        break

                if reels_count >= max_posts:
                    break

                if self.logger_manager is not None:
                    self.logger_manager.log_reels_scraped(username, reels_count)

                paging_info = paginated_reels_response["paging_info"]

            temp_file.flush()
        finally:
            temp_file.close()

        final_reels = []
        try:
            with open(temp_path, "r") as read_f:
                for line in read_f:
                    final_reels.append(json.loads(line.strip()))

        finally:
            os.remove(temp_path)

        if self.logger_manager is not None:
            self.logger_manager.log_account_success(username, reels_count)

        return final_reels

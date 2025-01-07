from typing import Dict, List, Optional
from reelscraper.utils import InstagramAPI, Extractor


class ReelScraper:
    """
    [ReelScraper] provides methods to gather Instagram Reels data via composition of [InstagramAPI] and [Extractor].

    :param [timeout]: Connection timeout in seconds
    :param [proxy]: Proxy string or None
    """

    def __init__(self, timeout: int, proxy: Optional[str]) -> None:
        """
        Initializes [ReelScraper] with an [InstagramAPI] and an [Extractor].

        :param [timeout]: Connection timeout in seconds
        :param [proxy]: Proxy string or None
        """
        self.api: InstagramAPI = InstagramAPI(timeout=timeout, proxy=proxy)
        self.extractor: Extractor = Extractor()

    def _fetch_reels(
        self, username: str, max_id: Optional[str], max_retries: int
    ) -> Dict:
        """
        Retrieves the first or paginated batch of reels. Returns a dictionary with items and paging info.
        Retries up to [max_retries] times if fetching fails.

        :param [username]: Username for which reels should be fetched
        :param [max_id]: Page identifier for subsequent requests (None for the first batch)
        :param [max_retries]: Maximum number of retry attempts
        :return: Dictionary containing reels items and paging info
        :raises Exception: If data cannot be fetched within [max_retries] attempts
        """
        response = None
        for _ in range(max_retries):
            if max_id is None:
                response = self.api.get_user_first_reels(username)
            else:
                response = self.api.get_user_paginated_reels(max_id, username)

            if response is not None:
                break

        if response is None:
            raise Exception(f"Error fetching reels for username: {username}")

        return response

    def get_user_reels(
        self, username: str, max_posts: Optional[int] = None, max_retries: int = 10
    ) -> List[Dict]:
        """
        Gathers user reels up to [max_posts] using retry logic. Paginates through all available reels.

        :param [username]: Username whose reels are requested
        :param [max_posts]: Maximum number of reels to fetch (default: 50)
        :param [max_retries]: Maximum number of retry attempts for each batch
        :return: List of reel information dictionaries
        :raises Exception: If initial reels cannot be fetched for [username]
        """
        reels: List[Dict] = []
        max_posts = max_posts if max_posts is not None else 50

        # Fetch first batch of reels
        first_reels_response = self._fetch_reels(
            username, max_id=None, max_retries=max_retries
        )
        first_reels: List[Dict] = first_reels_response["items"]
        paging_info: Dict = first_reels_response["paging_info"]

        for reel in first_reels:
            media: Dict = reel.get("media", {})
            reel_info: Optional[Dict] = self.extractor.extract_reel_info(media)
            if reel_info:
                reels.append(reel_info)
            if len(reels) >= max_posts:
                return reels

        # Check pagination availability
        while paging_info.get("more_available", False):
            max_id: str = paging_info.get("max_id", "")
            paginated_reels_response = self._fetch_reels(username, max_id, max_retries)
            paginated_reels: List[Dict] = paginated_reels_response["items"]

            for reel in paginated_reels:
                media: Dict = reel.get("media", {})
                reel_info: Optional[Dict] = self.extractor.extract_reel_info(media)
                if reel_info:
                    reels.append(reel_info)
                if len(reels) >= max_posts:
                    return reels

            paging_info = paginated_reels_response["paging_info"]

        return reels

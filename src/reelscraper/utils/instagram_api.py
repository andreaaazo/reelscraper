import json
import requests
from typing import Optional, Dict
from fake_useragent import UserAgent


class InstagramAPI:
    """
    InstagramAPI composes methods to interact with Instagram's endpoints.
    Encourages (COI), (DRY), (KISS), (YAGNI), (CCAC), (SRP), (OCP), (LSP), (ISP), (DIP).

    :param [timeout]: Timeout for HTTP requests in seconds.
    :param [proxy]: Proxy server address (optional).
    """

    BASE_URL = "https://www.instagram.com"
    GRAPHQL_URL = f"{BASE_URL}/graphql/query/"
    CLIPS_USER_URL = f"{BASE_URL}/api/v1/clips/user/"
    IG_APP_ID = "936619743392459"
    ASBD_ID = "129477"
    REQUEST_WITH = "XMLHttpRequest"
    QUERY_HASH = "58b6785bea111c67129decbe6a448951"

    def __init__(self, timeout: int = 40, proxy: Optional[str] = None):
        """
        __init__ sets initial parameters and configures proxy if provided.

        :param [timeout]: HTTP request timeout in seconds.
        :param [proxy]: Proxy server address, e.g., "user:pass@host:port".
        """
        self.timeout = timeout
        self.proxy = self._configure_proxy(proxy) if proxy else None
        self.csrf_token = None
        self.user_agent = UserAgent()

    def _configure_proxy(self, proxy: str) -> dict:
        """
        _configure_proxy constructs a dictionary for HTTP and HTTPS proxies.

        :param [proxy]: Proxy address string.
        :return: Dictionary containing proxy configurations.
        """
        return {
            "http": f"http://{proxy}",
            "https": f"https://{proxy}",
        }

    def _get_default_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        _get_default_headers builds default request headers with optional referer.

        :param [referer]: Referer URL string.
        :return: Dictionary of default HTTP headers.
        """
        headers = {
            "User-Agent": self.user_agent.random,
            "Accept": "application/json",
            "X-IG-App-ID": self.IG_APP_ID,
            "X-ASBD-ID": self.ASBD_ID,
            "X-Requested-With": self.REQUEST_WITH,
        }
        if referer:
            headers["Referer"] = referer
        return headers

    def _handle_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        **kwargs,
    ) -> Optional[Dict]:
        """
        _handle_request wraps requests.request to handle HTTP interactions safely.

        :param [method]: HTTP method (e.g. "get", "post").
        :param [url]: Target endpoint URL.
        :param [headers]: Dictionary of HTTP headers.
        :param [**kwargs]: Additional keyword args to pass to requests.
        :return: JSON response as a dictionary or None on failure.
        """
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=self.timeout,
                proxies=self.proxy,
                **kwargs,
            )
            if "csrftoken" in response.cookies:
                self.csrf_token = response.cookies["csrftoken"]
            return response.json()
        except (requests.RequestException, ValueError):
            return None

    def _get_user_id(self, base_data: Dict) -> Optional[str]:
        """
        _get_user_id extracts user's ID from base data.

        :param [base_data]: Dictionary containing user information.
        :return: User ID string or None if not found.
        """
        if base_data is None:
            return None
        return base_data.get("data", {}).get("user", {}).get("id")

    def _get_headers_for_reels(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        _get_headers_for_reels produces headers needed for reels endpoint calls.

        :param [referer]: Referer URL string for reels.
        :return: Dictionary of HTTP headers for reels calls.
        :raises Exception: If CSRF token is missing (need to make a GET request first).
        """
        headers = self._get_default_headers(referer)
        if self.csrf_token:
            headers["x-csrftoken"] = self.csrf_token
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            return headers
        raise Exception("CSRF Token empty, make a GET request first")

    def _fetch_reels(self, payload: Dict, referer: str) -> Optional[Dict]:
        """
        _fetch_reels sends a POST request to fetch reels data.

        :param [payload]: Dictionary with reels request data.
        :param [referer]: Referer URL string for reels endpoint.
        :return: JSON response as a dictionary or None on failure.
        """
        headers = self._get_headers_for_reels(referer)
        return self._handle_request(
            "post",
            self.CLIPS_USER_URL,
            headers=headers,
            data=payload,
        )

    def get_user_base_data(self, username: str) -> Optional[Dict]:
        """
        get_user_base_data fetches base profile data for a given username.

        :param [username]: Instagram username.
        :return: Dictionary with user data or None on failure.
        """
        url = f"{self.BASE_URL}/api/v1/users/web_profile_info/"
        headers = self._get_default_headers(referer=f"{self.BASE_URL}/{username}/")
        params = {"username": username}
        return self._handle_request("get", url, headers=headers, params=params)

    def get_user_paginated_data(self, user_id: str, end_cursor: str) -> Optional[Dict]:
        """
        get_user_paginated_data retrieves paginated media data for a user.

        :param [user_id]: Instagram user's ID string.
        :param [end_cursor]: Cursor for pagination.
        :return: Dictionary with paginated data or None on failure.
        """
        variables = {"id": user_id, "first": 12, "after": end_cursor}
        params = {
            "query_hash": self.QUERY_HASH,
            "variables": json.dumps(variables),
        }
        headers = self._get_default_headers()
        return self._handle_request(
            "get", self.GRAPHQL_URL, headers=headers, params=params
        )

    def get_user_first_reels(
        self, username: str, page_size: int = 11
    ) -> Optional[Dict]:
        """
        get_user_first_reels fetches first reels of a user's profile.

        :param [username]: Instagram username.
        :param [page_size]: Number of reels to fetch in a single request.
        :return: Dictionary with reels data or None on failure.
        """
        base_user_data = self.get_user_base_data(username)
        user_id = self._get_user_id(base_user_data)
        if not user_id:
            return None

        payload = {
            "target_user_id": user_id,
            "page_size": page_size,
            "include_feed_video": "true",
        }
        referer = f"{self.BASE_URL}/{username}/reels/"
        return self._fetch_reels(payload, referer)

    def get_user_paginated_reels(self, max_id: str, username: str) -> Optional[Dict]:
        """
        get_user_paginated_reels fetches subsequent reels pages based on max_id.

        :param [max_id]: Identifier to request next set of reels.
        :param [username]: Instagram username.
        :return: Dictionary with reels data or None on failure.
        """
        base_data = self.get_user_base_data(username)
        user_id = self._get_user_id(base_data)
        if not user_id:
            return None

        payload = {
            "target_user_id": user_id,
            "page_size": 11,
            "include_feed_video": "true",
            "max_id": max_id,
        }
        referer = f"{self.BASE_URL}/{username}/reels/"
        response = self._fetch_reels(payload, referer)
        if not response or "items" not in response:
            return None
        return response

import json
import re
import requests
from typing import Optional, Dict, Any
from fake_useragent import UserAgent


class InstagramAPI:
    """
    InstagramAPI provides endpoints to interact with Instagram's API.

    Utilizes composition for modular behaviors such as HTTP configuration.

    **Parameters:**
    - `[timeout]`: Timeout for HTTP requests in seconds.
    - `[proxy]`: Proxy server address (optional, e.g., "host:port" or "user:pass@host:port").
    """

    BASE_URL: str = "https://www.instagram.com"
    GRAPHQL_URL: str = f"{BASE_URL}/graphql/query/"
    CLIPS_USER_URL: str = f"{BASE_URL}/api/v1/clips/user/"
    IG_APP_ID: str = "936619743392459"
    ASBD_ID: str = "129477"
    REQUEST_WITH: str = "XMLHttpRequest"
    QUERY_HASH: str = "58b6785bea111c67129decbe6a448951"

    def __init__(
        self, timeout: Optional[int] = 40, proxy: Optional[str] = None
    ) -> None:
        """
        __init__ initializes parameters and configures proxy if provided.

        **Parameters:**
        - `[timeout]`: HTTP request timeout in seconds.
        - `[proxy]`: Proxy server address in string format.
        """
        self.timeout: Optional[int] = timeout
        self.proxy: Optional[Dict[str, str]] = (
            self._configure_proxy(proxy) if proxy else None
        )
        self.csrf_token: Optional[str] = None
        self.user_agent: UserAgent = UserAgent()

    def _configure_proxy(self, proxy: str) -> Dict[str, str]:
        """
        _configure_proxy constructs a dictionary for HTTP and HTTPS proxies.

        Validates proxy format against the patterns:
          - host:port
          - user:pass@host:port

        **Parameters:**
        - `[proxy]`: Proxy address string.

        **Returns:**
        - Dictionary with proxy configurations for both HTTP and HTTPS.

        **Raises:**
        - `ValueError`: If proxy string does not match the expected format or port is invalid.
        """
        pattern: str = (
            r"^(?:(?P<username>[\w\.\-_]+):(?P<password>[\w\.\-_]+)@)?(?P<host>[\w\.\-]+):(?P<port>\d+)$"
        )
        match = re.match(pattern, proxy)
        if not match:
            raise ValueError(
                "Invalid proxy provided. Expected format 'host:port' or 'user:pass@host:port'."
            )

        port: int = int(match.group("port"))
        if not (1 <= port <= 65535):
            raise ValueError("Invalid port number in proxy configuration.")

        return {
            "http": f"http://{proxy}",
            "https": f"https://{proxy}",
        }

    def _get_default_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        _get_default_headers constructs default HTTP headers.

        **Parameters:**
        - `[referer]`: Optional referer URL string.

        **Returns:**
        - Dictionary of default HTTP headers.
        """
        headers: Dict[str, str] = {
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
        self, method: str, url: str, headers: Dict[str, str], **kwargs: Any
    ) -> Optional[Dict]:
        """
        _handle_request wraps requests.request for safe HTTP interactions.

        **Parameters:**
        - `[method]`: HTTP method (e.g., "get", "post").
        - `[url]`: Target endpoint URL.
        - `[headers]`: Dictionary of HTTP headers.
        - `[**kwargs]`: Additional keyword arguments for requests.

        **Returns:**
        - Parsed JSON response as a dictionary, or None on error.
        """
        try:
            response: requests.Response = requests.request(
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
        except (requests.RequestException, json.JSONDecodeError, ValueError):
            return None

    def _get_user_id(self, base_data: Dict) -> Optional[str]:
        """
        _get_user_id extracts the user ID from provided base data.

        **Parameters:**
        - `[base_data]`: Dictionary containing user data.

        **Returns:**
        - User ID string if found, otherwise None.
        """
        if not base_data:
            return None
        return base_data.get("data", {}).get("user", {}).get("id")

    def _get_headers_for_reels(self, referer: Optional[str] = None) -> Dict[str, str]:
        """
        _get_headers_for_reels produces headers needed for reels API calls.

        Requires a previously obtained CSRF token.

        **Parameters:**
        - `[referer]`: Optional referer URL for reels.

        **Returns:**
        - Dictionary of HTTP headers for reels requests.

        **Raises:**
        - Exception: If CSRF token is missing; perform a GET request first.
        """
        headers: Dict[str, str] = self._get_default_headers(referer)
        if self.csrf_token:
            headers["x-csrftoken"] = self.csrf_token
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            return headers
        raise Exception("CSRF Token is missing; perform a GET request first")

    def _fetch_reels(self, payload: Dict[str, Any], referer: str) -> Optional[Dict]:
        """
        _fetch_reels sends a POST request to retrieve reels data.

        **Parameters:**
        - `[payload]`: Dictionary of data for the reels request.
        - `[referer]`: Referer URL string for the reels endpoint.

        **Returns:**
        - Dictionary with reels data if successful, otherwise None.
        """
        headers: Dict[str, str] = self._get_headers_for_reels(referer)
        return self._handle_request(
            method="post",
            url=self.CLIPS_USER_URL,
            headers=headers,
            data=payload,
        )

    def get_user_base_data(self, username: str) -> Optional[Dict]:
        """
        get_user_base_data fetches profile base data for a provided username.

        **Parameters:**
        - `[username]`: Instagram username.

        **Returns:**
        - Dictionary with user data if successful, otherwise None.
        """
        url: str = f"{self.BASE_URL}/api/v1/users/web_profile_info/"
        headers: Dict[str, str] = self._get_default_headers(
            referer=f"{self.BASE_URL}/{username}/"
        )
        params: Dict[str, str] = {"username": username}
        response: Optional[Dict] = self._handle_request(
            "get", url, headers=headers, params=params
        )

        if response is None or type(response) is not dict:
            return None
        if "data" in response:
            return response
        return None

    def get_user_paginated_data(self, user_id: str, end_cursor: str) -> Optional[Dict]:
        """
        get_user_paginated_data retrieves paginated media data for a user.

        **Parameters:**
        - `[user_id]`: Instagram user ID.
        - `[end_cursor]`: Pagination cursor for next batch of data.

        **Returns:**
        - Dictionary with paginated data if successful, otherwise None.
        """
        variables: Dict[str, Any] = {"id": user_id, "first": 12, "after": end_cursor}
        params: Dict[str, str] = {
            "query_hash": self.QUERY_HASH,
            "variables": json.dumps(variables),
        }
        headers: Dict[str, str] = self._get_default_headers()
        response: Optional[Dict] = self._handle_request(
            "get", self.GRAPHQL_URL, headers=headers, params=params
        )

        if response is None or type(response) is not dict:
            return None
        if "data" in response:
            return response
        return None

    def get_user_first_reels(
        self, username: str, page_size: int = 11
    ) -> Optional[Dict]:
        """
        get_user_first_reels retrieves the initial set of reels for a given user.

        **Parameters:**
        - `[username]`: Instagram username.
        - `[page_size]`: Number of reels to fetch per request.

        **Returns:**
        - Dictionary with reels data if successful, otherwise None.
        """
        base_user_data: Optional[Dict] = self.get_user_base_data(username)
        user_id: Optional[str] = self._get_user_id(base_user_data)
        if not user_id:
            return None

        payload: Dict[str, Any] = {
            "target_user_id": user_id,
            "page_size": page_size,
            "include_feed_video": "true",
        }
        referer: str = f"{self.BASE_URL}/{username}/reels/"
        response: Optional[Dict] = self._fetch_reels(payload, referer)
        if response is None and type(response) is not dict:
            return None
        if "items" in response:
            return response
        return None

    def get_user_paginated_reels(self, max_id: str, username: str) -> Optional[Dict]:
        """
        get_user_paginated_reels retrieves the next page of reels for a given user.

        **Parameters:**
        - `[max_id]`: Pagination identifier to fetch next reels.
        - `[username]`: Instagram username.

        **Returns:**
        - Dictionary with reels data if successful, otherwise None.
        """
        base_data: Optional[Dict] = self.get_user_base_data(username)
        user_id: Optional[str] = self._get_user_id(base_data)
        if not user_id:
            return None

        payload: Dict[str, Any] = {
            "target_user_id": user_id,
            "page_size": 11,
            "include_feed_video": "true",
            "max_id": max_id,
        }
        referer: str = f"{self.BASE_URL}/{username}/reels/"
        response: Optional[Dict] = self._fetch_reels(payload, referer)
        if response is None and type(response) is not dict:
            return None
        if "items" in response:
            return response
        return None

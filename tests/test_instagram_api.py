import unittest
from unittest.mock import patch, MagicMock
import requests

from reelscraper.utils import InstagramAPI


class TestInstagramAPI(unittest.TestCase):
    def setUp(self):
        """
        setUp is run before every test; we instantiate InstagramAPI here.
        """
        self.api = InstagramAPI(timeout=10, proxy="user:pass@127.0.0.1:8080")

    #
    # -------------------------------------------------------------------------
    # Test the constructor and proxy configuration
    # -------------------------------------------------------------------------
    #
    def test_init_with_proxy(self):
        """Test that the proxy is correctly configured when provided."""
        expected_proxy = {
            "http": "http://user:pass@127.0.0.1:8080",
            "https": "https://user:pass@127.0.0.1:8080",
        }
        self.assertEqual(self.api.proxy, expected_proxy)
        self.assertEqual(self.api.timeout, 10)

    def test_init_without_proxy(self):
        """Test that the proxy remains None if not provided."""
        api_no_proxy = InstagramAPI()
        self.assertIsNone(api_no_proxy.proxy)
        self.assertEqual(api_no_proxy.timeout, 40)

    #
    # -------------------------------------------------------------------------
    # Test internal helpers (_configure_proxy, _get_default_headers, etc.)
    # -------------------------------------------------------------------------
    #
    def test__configure_proxy(self):
        """Test the private _configure_proxy method explicitly."""
        proxy_str = "another_user:another_pass@localhost:9999"
        result = self.api._configure_proxy(proxy_str)
        expected = {
            "http": "http://another_user:another_pass@localhost:9999",
            "https": "https://another_user:another_pass@localhost:9999",
        }
        self.assertEqual(result, expected)

    @patch(
        "reelscraper.utils.instagram_api.UserAgent"
    )  # <-- patch where UserAgent is imported
    def test__get_default_headers(self, mock_ua):
        """
        Test that default headers include the correct keys and mocked User-Agent.
        """
        # Mock the user agent returned by fake_useragent
        mock_ua.return_value.random = "TestUserAgent/1.0"

        api = InstagramAPI()
        headers = api._get_default_headers(referer="https://www.instagram.com/example/")

        self.assertIn("User-Agent", headers)
        self.assertIn("Referer", headers)
        self.assertEqual(headers["User-Agent"], "TestUserAgent/1.0")
        self.assertEqual(headers["Referer"], "https://www.instagram.com/example/")

    def test__get_user_id(self):
        """Test that _get_user_id extracts the user ID from a nested dictionary."""
        base_data = {
            "data": {"user": {"id": "1234567890"}},
        }
        user_id = self.api._get_user_id(base_data)
        self.assertEqual(user_id, "1234567890")

        # Test None scenario
        self.assertIsNone(self.api._get_user_id(None))
        self.assertIsNone(self.api._get_user_id({}))  # missing data->user->id

    #
    # -------------------------------------------------------------------------
    # Test _handle_request and how it handles responses
    # -------------------------------------------------------------------------
    #
    @patch("requests.request")
    def test__handle_request_success(self, mock_request):
        """Test _handle_request on successful JSON response with CSRF token."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_response.cookies = {"csrftoken": "test_csrf_token"}
        mock_request.return_value = mock_response

        headers = {"Test": "Header"}
        response = self.api._handle_request("get", "http://test.com", headers=headers)

        self.assertEqual(response, {"key": "value"})
        self.assertEqual(self.api.csrf_token, "test_csrf_token")
        mock_request.assert_called_once_with(
            method="get",
            url="http://test.com",
            headers=headers,
            timeout=self.api.timeout,
            proxies=self.api.proxy,
        )

    @patch("requests.request")
    def test__handle_request_no_csrf_token(self, mock_request):
        """Test that CSRF token is not set if cookie is missing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_response.cookies = {}
        mock_request.return_value = mock_response

        response = self.api._handle_request("post", "http://test.com", headers={})
        self.assertEqual(response, {"ok": True})
        self.assertIsNone(self.api.csrf_token)

    @patch("requests.request")
    def test__handle_request_request_exception(self, mock_request):
        """Test that _handle_request returns None when requests raises an exception."""
        mock_request.side_effect = requests.RequestException("Connection Error")
        response = self.api._handle_request("get", "http://test.com", headers={})
        self.assertIsNone(response)

    @patch("requests.request")
    def test__handle_request_json_error(self, mock_request):
        """
        Test that _handle_request returns None if .json() fails
        or if the response is not valid JSON.
        """
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = mock_response

        response = self.api._handle_request("get", "http://test.com", headers={})
        self.assertIsNone(response)

    #
    # -------------------------------------------------------------------------
    # Test _get_headers_for_reels
    # -------------------------------------------------------------------------
    #
    @patch("fake_useragent.UserAgent")
    def test__get_headers_for_reels_no_csrf_raises(self, mock_ua):
        """
        Test that _get_headers_for_reels raises Exception if csrf_token is empty.
        """
        with self.assertRaises(Exception) as ctx:
            self.api._get_headers_for_reels()
        self.assertIn("CSRF Token empty", str(ctx.exception))

    @patch("reelscraper.utils.instagram_api.UserAgent")  # <-- same patch target
    def test__get_headers_for_reels_success(self, mock_ua):
        """
        Test that _get_headers_for_reels returns headers including the CSRF token
        and mocked User-Agent.
        """
        # Mock the user agent
        mock_ua.return_value.random = "MockedUA"

        api = InstagramAPI()
        api.csrf_token = "test_token"  # so it doesn't raise Exception

        reels_headers = api._get_headers_for_reels(
            "https://www.instagram.com/user/reels/"
        )

        self.assertEqual(reels_headers["x-csrftoken"], "test_token")
        self.assertEqual(
            reels_headers["Content-Type"], "application/x-www-form-urlencoded"
        )
        self.assertIn("User-Agent", reels_headers)
        self.assertEqual(reels_headers["User-Agent"], "MockedUA")

    #
    # -------------------------------------------------------------------------
    # Test _fetch_reels
    # -------------------------------------------------------------------------
    #
    @patch.object(InstagramAPI, "_handle_request")
    @patch.object(InstagramAPI, "_get_headers_for_reels")
    def test__fetch_reels(self, mock_get_headers, mock_handle_request):
        """Test _fetch_reels calls _handle_request with correct args."""
        mock_get_headers.return_value = {"Header": "Value"}
        mock_handle_request.return_value = {"reels": []}

        payload = {"target_user_id": "123", "page_size": 11}
        referer = "https://www.instagram.com/user/reels/"
        response = self.api._fetch_reels(payload, referer)

        self.assertEqual(response, {"reels": []})
        mock_get_headers.assert_called_once_with(referer)
        mock_handle_request.assert_called_once_with(
            "post",
            self.api.CLIPS_USER_URL,
            headers={"Header": "Value"},
            data=payload,
        )

    #
    # -------------------------------------------------------------------------
    # Test get_user_base_data
    # -------------------------------------------------------------------------
    #
    @patch.object(InstagramAPI, "_handle_request")
    def test_get_user_base_data(self, mock_handle_request):
        """Test get_user_base_data sends correct params and returns response."""
        mock_handle_request.return_value = {"data": "user_base"}
        username = "testuser"
        response = self.api.get_user_base_data(username)
        self.assertEqual(response, {"data": "user_base"})

        # Check the URL and params passed to _handle_request
        expected_url = f"{self.api.BASE_URL}/api/v1/users/web_profile_info/"
        expected_referer = f"{self.api.BASE_URL}/{username}/"
        mock_handle_request.assert_called_once()
        args, kwargs = mock_handle_request.call_args
        self.assertEqual(args[0], "get")
        self.assertEqual(args[1], expected_url)
        self.assertIn("headers", kwargs)
        self.assertIn("params", kwargs)
        self.assertEqual(kwargs["params"], {"username": "testuser"})
        self.assertIn(expected_referer, kwargs["headers"].get("Referer", ""))

    #
    # -------------------------------------------------------------------------
    # Test get_user_paginated_data
    # -------------------------------------------------------------------------
    #
    @patch.object(InstagramAPI, "_handle_request")
    def test_get_user_paginated_data(self, mock_handle_request):
        """Test get_user_paginated_data builds query params and returns response."""
        mock_handle_request.return_value = {"data": "paginated_user_data"}
        user_id = "98765"
        end_cursor = "end_cursor_string"
        response = self.api.get_user_paginated_data(user_id, end_cursor)
        self.assertEqual(response, {"data": "paginated_user_data"})

        mock_handle_request.assert_called_once()
        args, kwargs = mock_handle_request.call_args
        self.assertEqual(args[0], "get")
        self.assertEqual(args[1], self.api.GRAPHQL_URL)
        self.assertIn("params", kwargs)
        query_params = kwargs["params"]
        self.assertEqual(query_params["query_hash"], self.api.QUERY_HASH)
        self.assertIn("variables", query_params)
        self.assertIn("first", query_params["variables"])
        self.assertIn("after", query_params["variables"])

    #
    # -------------------------------------------------------------------------
    # Test get_user_first_reels
    # -------------------------------------------------------------------------
    #
    @patch.object(InstagramAPI, "_fetch_reels")
    @patch.object(InstagramAPI, "_get_user_id")
    @patch.object(InstagramAPI, "get_user_base_data")
    def test_get_user_first_reels_valid(
        self, mock_get_user_base_data, mock_get_user_id, mock_fetch_reels
    ):
        """Test get_user_first_reels returns reels data when everything is valid."""
        mock_get_user_base_data.return_value = {"data": "some_base_data"}
        mock_get_user_id.return_value = "111222333"
        mock_fetch_reels.return_value = {"items": ["reel1", "reel2"]}

        reels_data = self.api.get_user_first_reels("someuser", page_size=5)
        self.assertEqual(reels_data, {"items": ["reel1", "reel2"]})

        mock_get_user_base_data.assert_called_with("someuser")
        mock_get_user_id.assert_called_with({"data": "some_base_data"})
        mock_fetch_reels.assert_called_once()
        # Check payload in _fetch_reels call
        args, kwargs = mock_fetch_reels.call_args
        payload_arg = args[0]
        referer_arg = args[1]
        self.assertEqual(payload_arg["target_user_id"], "111222333")
        self.assertEqual(payload_arg["page_size"], 5)
        self.assertTrue("include_feed_video" in payload_arg)
        self.assertIn("someuser/reels", referer_arg)

    @patch.object(InstagramAPI, "_fetch_reels")
    @patch.object(InstagramAPI, "_get_user_id")
    @patch.object(InstagramAPI, "get_user_base_data")
    def test_get_user_first_reels_no_user_id(
        self, mock_get_user_base_data, mock_get_user_id, mock_fetch_reels
    ):
        """Test get_user_first_reels returns None if user_id is missing."""
        mock_get_user_base_data.return_value = {"data": "some_base_data"}
        mock_get_user_id.return_value = None  # no ID
        reels_data = self.api.get_user_first_reels("someuser")
        self.assertIsNone(reels_data)
        mock_fetch_reels.assert_not_called()

    #
    # -------------------------------------------------------------------------
    # Test get_user_paginated_reels
    # -------------------------------------------------------------------------
    #
    @patch.object(InstagramAPI, "_fetch_reels")
    @patch.object(InstagramAPI, "_get_user_id")
    @patch.object(InstagramAPI, "get_user_base_data")
    def test_get_user_paginated_reels_success(
        self, mock_get_user_base_data, mock_get_user_id, mock_fetch_reels
    ):
        """Test get_user_paginated_reels returns reels data on success."""
        mock_get_user_base_data.return_value = {"data": "base_data"}
        mock_get_user_id.return_value = "444555666"
        mock_fetch_reels.return_value = {"items": ["reelA", "reelB"]}

        max_id = "abc123"
        reels_data = self.api.get_user_paginated_reels(max_id, "someuser")
        self.assertEqual(reels_data, {"items": ["reelA", "reelB"]})

        mock_get_user_base_data.assert_called_with("someuser")
        mock_get_user_id.assert_called_with({"data": "base_data"})
        mock_fetch_reels.assert_called_once()
        args, kwargs = mock_fetch_reels.call_args
        self.assertEqual(args[0]["max_id"], "abc123")

    @patch.object(InstagramAPI, "_fetch_reels")
    @patch.object(InstagramAPI, "_get_user_id")
    @patch.object(InstagramAPI, "get_user_base_data")
    def test_get_user_paginated_reels_no_user_id(
        self, mock_get_user_base_data, mock_get_user_id, mock_fetch_reels
    ):
        """Test get_user_paginated_reels returns None if user_id is missing."""
        mock_get_user_base_data.return_value = {}
        mock_get_user_id.return_value = None
        reels_data = self.api.get_user_paginated_reels("max_id", "someuser")
        self.assertIsNone(reels_data)
        mock_fetch_reels.assert_not_called()

    @patch.object(InstagramAPI, "_fetch_reels")
    @patch.object(InstagramAPI, "_get_user_id")
    @patch.object(InstagramAPI, "get_user_base_data")
    def test_get_user_paginated_reels_missing_items(
        self, mock_get_user_base_data, mock_get_user_id, mock_fetch_reels
    ):
        """
        Test get_user_paginated_reels returns None if the response is missing 'items'.
        """
        mock_get_user_base_data.return_value = {"data": "base_data"}
        mock_get_user_id.return_value = "999"
        mock_fetch_reels.return_value = {"something_else": True}  # no 'items'

        reels_data = self.api.get_user_paginated_reels("max_id", "someuser")
        self.assertIsNone(reels_data)

    #
    # -------------------------------------------------------------------------
    # End of tests
    # -------------------------------------------------------------------------
    #

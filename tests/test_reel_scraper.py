import unittest
from typing import Dict, List, Optional

# Import the class under test.
from reelscraper import ReelScraper

# Dummy implementations of dependencies:


class DummyInstagramAPI:
    """
    Dummy InstagramAPI implementation that returns preset responses.
    The responses list is consumed sequentially with each call to a reels-fetch method.
    """

    def __init__(self, responses: List[Optional[Dict]]):
        self.responses = responses
        self.call_count = 0

    def get_user_first_reels(
        self, username: str, page_size: int = 11
    ) -> Optional[Dict]:
        response = self._next_response()
        return response

    def get_user_paginated_reels(self, max_id: str, username: str) -> Optional[Dict]:
        response = self._next_response()
        return response

    def _next_response(self) -> Optional[Dict]:
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return None


class DummyExtractor:
    """
    Dummy Extractor that simulates extracting reel info.
    It returns a dictionary with the media data nested under a key 'reel'
    if the media data contains a key 'valid' set to True.
    """

    def extract_reel_info(self, media: Dict) -> Optional[Dict]:
        if media.get("valid"):
            # Return a dummy extracted structure that allows identifying the reel by code.
            return {"reel": media}
        return None


class DummyLoggerManager:
    """
    Dummy LoggerManager that records all logging calls in a list.
    """

    def __init__(self):
        self.calls = []

    def log_account_error(self, account_name: str):
        self.calls.append(("error", account_name))

    def log_retry(self, retry: int, max_retries: int, account_name: str):
        self.calls.append(("retry", retry, max_retries, account_name))

    def log_account_success(self, username: str, reel_count: int):
        self.calls.append(("success", username, reel_count))

    def log_account_begin(self, username: str):
        self.calls.append(("begin", username))


# The unit tests for ReelScraper
class TestReelScraper(unittest.TestCase):
    def setUp(self):
        self.username = "testuser"
        self.logger = DummyLoggerManager()

    def test_get_user_reels_single_batch(self):
        """
        Test that get_user_reels returns the expected number of reels from a single batch.
        This batch is set to return two reels and no further pagination.
        """
        response = {
            "items": [
                {
                    "media": {
                        "valid": True,
                        "code": "abc",
                        "like_count": 10,
                        "comment_count": 2,
                        "play_count": 100,
                        "taken_at": 1610000000,
                        "video_duration": 30,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
                {
                    "media": {
                        "valid": True,
                        "code": "def",
                        "like_count": 20,
                        "comment_count": 3,
                        "play_count": 200,
                        "taken_at": 1610000100,
                        "video_duration": 25,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
            ],
            "paging_info": {"more_available": False},
        }

        dummy_api = DummyInstagramAPI([response])
        dummy_extractor = DummyExtractor()
        rs = ReelScraper(timeout=10, proxy=None, logger_manager=self.logger)
        rs.api = dummy_api  # Override with dummy API
        rs.extractor = dummy_extractor  # Override with dummy Extractor

        result = rs.get_user_reels(self.username, max_posts=2, max_retries=1)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["reel"]["code"], "abc")
        self.assertEqual(result[1]["reel"]["code"], "def")

        # Verify that both begin and success logs were recorded.
        self.assertIn(("begin", self.username), self.logger.calls)
        self.assertIn(("success", self.username, 2), self.logger.calls)

    def test_get_user_reels_multiple_batches(self):
        """
        Test that get_user_reels correctly concatenates reels across paginated responses.
        The first batch returns one reel and signals more data is available, and the second batch
        returns two additional reels.
        """
        response1 = {
            "items": [
                {
                    "media": {
                        "valid": True,
                        "code": "abc",
                        "like_count": 10,
                        "comment_count": 2,
                        "play_count": 100,
                        "taken_at": 1610000000,
                        "video_duration": 30,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
            ],
            "paging_info": {"more_available": True, "max_id": "page2"},
        }
        response2 = {
            "items": [
                {
                    "media": {
                        "valid": True,
                        "code": "def",
                        "like_count": 20,
                        "comment_count": 3,
                        "play_count": 200,
                        "taken_at": 1610000100,
                        "video_duration": 25,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
                {
                    "media": {
                        "valid": True,
                        "code": "ghi",
                        "like_count": 30,
                        "comment_count": 4,
                        "play_count": 300,
                        "taken_at": 1610000200,
                        "video_duration": 35,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
            ],
            "paging_info": {"more_available": False},
        }

        dummy_api = DummyInstagramAPI([response1, response2])
        dummy_extractor = DummyExtractor()
        rs = ReelScraper(timeout=10, proxy=None, logger_manager=self.logger)
        rs.api = dummy_api
        rs.extractor = dummy_extractor

        result = rs.get_user_reels(self.username, max_posts=3, max_retries=1)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["reel"]["code"], "abc")
        self.assertEqual(result[1]["reel"]["code"], "def")
        self.assertEqual(result[2]["reel"]["code"], "ghi")

    def test_fetch_reels_failure_triggers_exception(self):
        """
        Test that get_user_reels raises an exception if no valid response is obtained
        after the specified number of retry attempts, and that the error is logged.
        """
        dummy_api = DummyInstagramAPI([None, None])
        dummy_extractor = DummyExtractor()
        rs = ReelScraper(timeout=10, proxy=None, logger_manager=self.logger)
        rs.api = dummy_api
        rs.extractor = dummy_extractor

        with self.assertRaises(Exception) as context:
            rs.get_user_reels(self.username, max_posts=1, max_retries=2)
        self.assertIn("Error fetching reels for username", str(context.exception))
        self.assertIn(
            ("error", self.username),
            self.logger.calls,
        )

    def test_get_user_reels_with_invalid_reels(self):
        """
        Test that reels with invalid media (i.e. extraction returns None) are skipped.
        Only reels that pass extraction should be returned.
        """
        response = {
            "items": [
                {
                    "media": {
                        "valid": False,  # This reel should be skipped.
                        "code": "invalid1",
                    }
                },
                {
                    "media": {
                        "valid": True,
                        "code": "valid1",
                        "like_count": 50,
                        "comment_count": 5,
                        "play_count": 500,
                        "taken_at": 1610000300,
                        "video_duration": 40,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
                {
                    "media": {
                        "valid": False,  # Should be skipped.
                        "code": "invalid2",
                    }
                },
            ],
            "paging_info": {"more_available": False},
        }

        dummy_api = DummyInstagramAPI([response])
        dummy_extractor = DummyExtractor()
        rs = ReelScraper(timeout=10, proxy=None, logger_manager=self.logger)
        rs.api = dummy_api
        rs.extractor = dummy_extractor

        result = rs.get_user_reels(self.username, max_posts=3, max_retries=1)
        # Only one valid reel should be returned.
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["reel"]["code"], "valid1")

    def test_get_user_reels_retry_logic_succeeds_after_failures(self):
        """
        Test that if the first few attempts to fetch reels return None, the retry logic
        continues until a valid response is retrieved.
        """
        # First two responses are None, then a valid response.
        valid_response = {
            "items": [
                {
                    "media": {
                        "valid": True,
                        "code": "retry_success",
                        "like_count": 70,
                        "comment_count": 7,
                        "play_count": 700,
                        "taken_at": 1610000400,
                        "video_duration": 45,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
            ],
            "paging_info": {"more_available": False},
        }
        dummy_api = DummyInstagramAPI([None, None, valid_response])
        dummy_extractor = DummyExtractor()
        rs = ReelScraper(timeout=10, proxy=None, logger_manager=self.logger)
        rs.api = dummy_api
        rs.extractor = dummy_extractor

        result = rs.get_user_reels(self.username, max_posts=1, max_retries=3)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["reel"]["code"], "retry_success")
        # Confirm that one retry were logged.
        retry_logs = [call for call in self.logger.calls if call[0] == "retry"]
        self.assertEqual(len(retry_logs), 1)

    def test_get_user_reels_stops_at_max_posts_limit(self):
        """
        Test that get_user_reels stops fetching more reels as soon as the max_posts limit is reached,
        even if more reels are available.
        """
        # First batch returns three valid reels, but we only want two.
        response = {
            "items": [
                {
                    "media": {
                        "valid": True,
                        "code": "reel1",
                        "like_count": 15,
                        "comment_count": 1,
                        "play_count": 150,
                        "taken_at": 1610000500,
                        "video_duration": 20,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
                {
                    "media": {
                        "valid": True,
                        "code": "reel2",
                        "like_count": 25,
                        "comment_count": 2,
                        "play_count": 250,
                        "taken_at": 1610000600,
                        "video_duration": 22,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
                {
                    "media": {
                        "valid": True,
                        "code": "reel3",
                        "like_count": 35,
                        "comment_count": 3,
                        "play_count": 350,
                        "taken_at": 1610000700,
                        "video_duration": 24,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
            ],
            "paging_info": {"more_available": True, "max_id": "page2"},
        }
        # Second batch (should not be fetched because max_posts is reached in the first batch).
        response_page2 = {
            "items": [
                {
                    "media": {
                        "valid": True,
                        "code": "reel4",
                        "like_count": 45,
                        "comment_count": 4,
                        "play_count": 450,
                        "taken_at": 1610000800,
                        "video_duration": 26,
                        "original_width": 640,
                        "original_height": 480,
                        "number_of_qualities": 2,
                        "owner": {"username": self.username},
                    }
                },
            ],
            "paging_info": {"more_available": False},
        }

        dummy_api = DummyInstagramAPI([response, response_page2])
        dummy_extractor = DummyExtractor()
        rs = ReelScraper(timeout=10, proxy=None, logger_manager=self.logger)
        rs.api = dummy_api
        rs.extractor = dummy_extractor

        # Request only 2 reels.
        result = rs.get_user_reels(self.username, max_posts=2, max_retries=1)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["reel"]["code"], "reel1")
        self.assertEqual(result[1]["reel"]["code"], "reel2")
        # Verify that after reaching max_posts the success log reflects 2 reels.
        self.assertIn(("success", self.username, 2), self.logger.calls)


if __name__ == "__main__":
    unittest.main()

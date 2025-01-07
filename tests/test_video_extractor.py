import unittest
from reelscraper.utils import Extractor


class TestExtractor(unittest.TestCase):

    #
    # -------------------------------------------------------------------------
    # Existing tests for parse_iso8601_duration
    # -------------------------------------------------------------------------
    #
    def test_parse_iso8601_duration_full(self):
        """Test parsing a full ISO 8601 duration (hours, minutes, seconds)."""
        duration_str = "PT1H2M18.100S"
        expected = 3600 + 120 + 18.100  # 3738.1
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertAlmostEqual(result, expected)

    def test_parse_iso8601_duration_missing_hours(self):
        """Test parsing an ISO 8601 duration with no hours."""
        duration_str = "PT2M18.100S"
        expected = 120 + 18.100  # 138.1
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertAlmostEqual(result, expected)

    def test_parse_iso8601_duration_only_hours(self):
        duration_str = "PT1H"
        expected = 3600.0
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertAlmostEqual(result, expected)

    def test_parse_iso8601_duration_only_minutes(self):
        duration_str = "PT2M"
        expected = 120.0
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertAlmostEqual(result, expected)

    def test_parse_iso8601_duration_zero(self):
        duration_str = "PT0H0M0S"
        expected = 0.0
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertAlmostEqual(result, expected)

    def test_parse_iso8601_duration_fractional_hours(self):
        duration_str = "PT1.5H"
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertIsNone(result, "Should return None for fractional hours.")

    def test_parse_iso8601_duration_missing_PT(self):
        duration_str = "1H2M3S"
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertIsNone(result, "Should return None when 'PT' is missing.")

    def test_parse_iso8601_duration_only_seconds(self):
        """Test parsing an ISO 8601 duration with only seconds."""
        duration_str = "PT18.100S"
        expected = 18.100
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertAlmostEqual(result, expected)

    def test_parse_iso8601_duration_invalid(self):
        """Test parsing an invalid ISO 8601 duration string."""
        duration_str = "InvalidDuration"
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertIsNone(result)

    def test_parse_iso8601_duration_empty(self):
        """Test parsing an empty ISO 8601 duration string."""
        duration_str = ""
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertIsNone(result)

    def test_parse_iso8601_duration_negative_duration(self):
        """Test parsing a negative ISO 8601 duration, which should fail."""
        duration_str = "PT-1H"
        result = Extractor.parse_iso8601_duration(duration_str)
        self.assertIsNone(result)

    #
    # -------------------------------------------------------------------------
    # Existing tests for get_video_duration
    # -------------------------------------------------------------------------
    #
    def test_get_video_duration_valid(self):
        """Test get_video_duration with a valid XML dash manifest."""
        xml_manifest = '<Manifest mediaPresentationDuration="PT1H2M18.100S"></Manifest>'
        node = {"dash_info": {"video_dash_manifest": xml_manifest}}
        expected_duration = 3600 + 120 + 18.100  # 3738.1
        result = Extractor.get_video_duration(node)
        self.assertAlmostEqual(result, expected_duration)

    def test_get_video_duration_missing_dash_info(self):
        """Test get_video_duration with missing dash_info."""
        node = {}
        result = Extractor.get_video_duration(node)
        self.assertIsNone(result)

    def test_get_video_duration_invalid_xml(self):
        """Test get_video_duration with invalid XML."""
        xml_manifest = "InvalidXML"
        node = {"dash_info": {"video_dash_manifest": xml_manifest}}
        result = Extractor.get_video_duration(node)
        self.assertIsNone(result)

    def test_get_video_duration_missing_duration(self):
        """Test get_video_duration with no mediaPresentationDuration attribute."""
        xml_manifest = (
            '<?xml version="1.0"?><MPD xmlns="urn:mpeg:dash:schema:mpd:2011" '
            'minBufferTime="PT1.500S" type="static" maxSegmentDuration="PT0H0M5.000S" '
            'profiles="urn:mpeg:dash:profile:isoff-on-demand:2011,http://dashif.org/guidelines/dash264" '
            'FBManifestIdentifier="some_identifier"></MPD>'
        )
        node = {"dash_info": {"video_dash_manifest": xml_manifest}}
        result = Extractor.get_video_duration(node)
        self.assertIsNone(result)

    def test_get_video_duration_invalid_format(self):
        """Test get_video_duration with an unparseable duration string."""
        xml_manifest = '<Manifest mediaPresentationDuration="1H2M3S"></Manifest>'
        node = {
            "dash_info": {"video_dash_manifest": xml_manifest},
        }
        result = Extractor.get_video_duration(node)
        self.assertIsNone(result)

    #
    # -------------------------------------------------------------------------
    # Existing tests for extract_video_info
    # -------------------------------------------------------------------------
    #
    def test_extract_video_info_valid(self):
        """Test extract_video_info with valid data."""
        xml_manifest = (
            '<?xml version="1.0"?><MPD xmlns="urn:mpeg:dash:schema:mpd:2011" '
            'mediaPresentationDuration="PT0H2M58.210S"></MPD>'
        )
        node = {
            "is_video": True,
            "video_url": "http://example.com/video.mp4",
            "edge_media_preview_like": {"count": 100},
            "edge_media_to_comment": {"count": 20},
            "video_view_count": 1000,
            "taken_at_timestamp": 1_600_000_000,  # Valid timestamp
            "dimensions": {"width": 1920, "height": 1080},
            "shortcode": "ABC123",
            "dash_info": {"video_dash_manifest": xml_manifest},
        }
        expected = {
            "url": "http://example.com/video.mp4",
            "shortcode": "ABC123",
            "likes": 100,
            "comments": 20,
            "views": 1000,
            "posted_time": 1_600_000_000,
            "video_duration": 178.21,
            "dimensions": {
                "width": 1920,
                "height": 1080,
            },
        }
        result = Extractor.extract_video_info(node)
        self.assertEqual(result, expected)

    def test_extract_video_info_not_a_video(self):
        """Test extract_video_info when is_video is False."""
        node = {"is_video": False}
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

    def test_extract_video_info_likes_negative(self):
        """Test extract_video_info when likes is -1."""
        node = {
            "is_video": True,
            "edge_media_preview_like": {"count": -1},
            "taken_at_timestamp": 1_600_000_000,
            "dash_info": {
                "video_dash_manifest": '<Manifest mediaPresentationDuration="PT18.100S"></Manifest>'
            },
        }
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

    def test_extract_video_info_posted_time_invalid(self):
        """
        Test extract_video_info with an invalid posted_time (<= 1_000_000_000)
        or non-numeric.
        """
        node = {
            "is_video": True,
            "edge_media_preview_like": {"count": 100},
            "taken_at_timestamp": 999_999_999,  # Too small
            "dash_info": {
                "video_dash_manifest": '<Manifest mediaPresentationDuration="PT18.100S"></Manifest>'
            },
        }
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

    def test_extract_video_info_missing_duration(self):
        """Test extract_video_info when duration is missing or unparseable."""
        node = {
            "is_video": True,
            "video_url": "http://example.com/video.mp4",
            "edge_media_preview_like": {"count": 100},
            "edge_media_to_comment": {"count": 20},
            "video_view_count": 1000,
            "taken_at_timestamp": 1_600_000_000,
            "dimensions": {"width": 1920, "height": 1080},
            "shortcode": "ABC123",
            "dash_info": {"video_dash_manifest": "<Manifest></Manifest>"},
        }
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

    def test_extract_video_info_invalid_duration(self):
        """Test extract_video_info with an invalid duration string."""
        node = {
            "is_video": True,
            "video_url": "http://example.com/video.mp4",
            "edge_media_preview_like": {"count": 100},
            "edge_media_to_comment": {"count": 20},
            "video_view_count": 1000,
            "taken_at_timestamp": 1_600_000_000,
            "dimensions": {"width": 1920, "height": 1080},
            "shortcode": "ABC123",
            "dash_info": {
                "video_dash_manifest": '<Manifest mediaPresentationDuration="InvalidDuration"></Manifest>'
            },
        }
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

    def test_extract_video_info_missing_fields(self):
        """Test extract_video_info when some fields are missing."""
        node = {
            "is_video": True,
            # "video_url" is missing
            "edge_media_preview_like": {"count": 100},
            # "edge_media_to_comment" is missing
            # "video_view_count" is missing
            "taken_at_timestamp": 1_600_000_000,
            "dimensions": {"width": 1920},
            "shortcode": "ABC123",
            "dash_info": {
                "video_dash_manifest": '<Manifest mediaPresentationDuration="PT18.100S"></Manifest>'
            },
        }
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

    def test_extract_video_info_missing_is_video(self):
        """Test extract_video_info when 'is_video' key is missing or not a boolean."""
        node = {
            "video_url": "http://example.com/video.mp4",
            "edge_media_preview_like": {"count": 100},
            "edge_media_to_comment": {"count": 20},
            "video_view_count": 1000,
            "taken_at_timestamp": 1_600_000_000,
            "dimensions": {"width": 1920, "height": 1080},
            "shortcode": "ABC123",
            "dash_info": {
                "video_dash_manifest": '<Manifest mediaPresentationDuration="PT18.100S"></Manifest>'
            },
        }
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

        node["is_video"] = "yes"
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

    def test_extract_video_info_missing_posted_time(self):
        """Test extract_video_info with missing or invalid posted_time."""
        node = {
            "is_video": True,
            "video_url": "http://example.com/video.mp4",
            "edge_media_preview_like": {"count": 100},
            "edge_media_to_comment": {"count": 20},
            "video_view_count": 1000,
            # "taken_at_timestamp" missing
            "dimensions": {"width": 1920, "height": 1080},
            "shortcode": "ABC123",
            "dash_info": {
                "video_dash_manifest": '<Manifest mediaPresentationDuration="PT18.100S"></Manifest>'
            },
        }
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

        node["taken_at_timestamp"] = "not_a_timestamp"
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

    def test_extract_video_info_missing_dash_info(self):
        """Test extract_video_info with missing or empty dash_info."""
        node = {
            "is_video": True,
            "video_url": "http://example.com/video.mp4",
            "edge_media_preview_like": {"count": 100},
            "edge_media_to_comment": {"count": 20},
            "video_view_count": 1000,
            "taken_at_timestamp": 1_600_000_000,
            "dimensions": {"width": 1920, "height": 1080},
            "shortcode": "ABC123",
            # "dash_info" missing
        }
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

        node["dash_info"] = {}
        result = Extractor.extract_video_info(node)
        self.assertIsNone(result)

    def test_extract_video_info_invalid_dimensions(self):
        """Test extract_video_info with dimensions provided as strings."""
        node = {
            "is_video": True,
            "video_url": "http://example.com/video.mp4",
            "edge_media_preview_like": {"count": 100},
            "edge_media_to_comment": {"count": 20},
            "video_view_count": 1000,
            "taken_at_timestamp": 1_600_000_000,
            "dimensions": {"width": "1920", "height": "1080"},  # string values
            "shortcode": "ABC123",
            "dash_info": {
                "video_dash_manifest": '<Manifest mediaPresentationDuration="PT18.100S"></Manifest>'
            },
        }
        expected = {
            "url": "http://example.com/video.mp4",
            "shortcode": "ABC123",
            "likes": 100,
            "comments": 20,
            "views": 1000,
            "posted_time": 1_600_000_000,
            "video_duration": 18.100,
            "dimensions": {
                "width": 1920,
                "height": 1080,
            },
        }
        result = Extractor.extract_video_info(node)
        self.assertEqual(result, expected)

    def test_extract_video_info_non_numeric_counts(self):
        """Test extract_video_info with numeric fields provided as strings."""
        node = {
            "is_video": True,
            "video_url": "http://example.com/video.mp4",
            "edge_media_preview_like": {"count": "100"},
            "edge_media_to_comment": {"count": "20"},
            "video_view_count": "1000",
            "taken_at_timestamp": 1_600_000_000,
            "dimensions": {"width": 1920, "height": 1080},
            "shortcode": "ABC123",
            "dash_info": {
                "video_dash_manifest": '<Manifest mediaPresentationDuration="PT18.100S"></Manifest>'
            },
        }
        expected = {
            "url": "http://example.com/video.mp4",
            "shortcode": "ABC123",
            "likes": 100,
            "comments": 20,
            "views": 1000,
            "posted_time": 1_600_000_000,
            "video_duration": 18.100,
            "dimensions": {
                "width": 1920,
                "height": 1080,
            },
        }
        result = Extractor.extract_video_info(node)
        self.assertEqual(result, expected)

    #
    # -------------------------------------------------------------------------
    # NEW tests for extract_reel_info
    # -------------------------------------------------------------------------
    #
    def test_extract_reel_info_valid(self):
        """Test extract_reel_info with all valid fields."""
        media = {
            "code": "XYZ789",
            "like_count": 150,
            "comment_count": 25,
            "play_count": 2000,
            "taken_at": 1_650_000_000,
            "video_duration": 30,
            "original_width": 1080,
            "original_height": 1920,
            "number_of_qualities": 3,
            "owner": {"username": "testuser"},
        }
        result = Extractor().extract_reel_info(media)
        expected = {
            "url": "https://www.instagram.com/reel/XYZ789",
            "shortcode": "XYZ789",
            "username": "testuser",
            "likes": 150,
            "comments": 25,
            "views": 2000,
            "posted_time": 1_650_000_000,
            "video_duration": 30,
            "numbers_of_qualities": 3,
            "dimensions": {
                "width": 1080,
                "height": 1920,
            },
        }
        self.assertEqual(result, expected)

    def test_extract_reel_info_missing_owner(self):
        """Test extract_reel_info when owner is missing."""
        media = {
            "code": "XYZ789",
            "like_count": 150,
            "comment_count": 25,
            "play_count": 2000,
            "taken_at": 1_650_000_000,
            "video_duration": 30,
            "original_width": 1080,
            "original_height": 1920,
            "number_of_qualities": 3,
            # "owner" is missing
        }
        result = Extractor().extract_reel_info(media)
        self.assertIsNone(result, "Should return None when owner is missing.")

    def test_extract_reel_info_missing_username(self):
        """Test extract_reel_info when owner's username is missing."""
        media = {
            "code": "XYZ789",
            "like_count": 150,
            "comment_count": 25,
            "play_count": 2000,
            "taken_at": 1_650_000_000,
            "video_duration": 30,
            "original_width": 1080,
            "original_height": 1920,
            "number_of_qualities": 3,
            "owner": {},  # no "username"
        }
        result = Extractor().extract_reel_info(media)
        self.assertIsNone(
            result, "Should return None when username is missing in owner."
        )

    def test_extract_reel_info_missing_fields(self):
        """Test extract_reel_info when required fields are missing."""
        # missing code, like_count, etc.
        media = {"owner": {"username": "testuser"}}
        result = Extractor().extract_reel_info(media)
        self.assertIsNone(result)

    def test_extract_reel_info_invalid_field_types(self):
        """Test extract_reel_info when fields have invalid types."""
        media = {
            "code": 123,  # Should be str
            "like_count": "150",  # Should be int or float
            "comment_count": "25",
            "play_count": "2000",
            "taken_at": "1_650_000_000",
            "video_duration": "30",
            "original_width": "1080",
            "original_height": "1920",
            "number_of_qualities": "3",
            "owner": {"username": "testuser"},
        }
        result = Extractor().extract_reel_info(media)
        self.assertIsNone(result, "Should return None for invalid field types.")

    def test_extract_reel_info_empty_media(self):
        """Test extract_reel_info with an empty dict."""
        media = {}
        result = Extractor().extract_reel_info(media)
        self.assertIsNone(result, "Should return None when media is empty.")

    #
    # -------------------------------------------------------------------------
    # End of tests
    # -------------------------------------------------------------------------
    #

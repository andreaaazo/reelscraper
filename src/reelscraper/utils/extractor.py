import re
import xml.etree.ElementTree as ET
from typing import Optional, Dict


class Extractor:
    """
    VideoExtractor composes utility methods to parse Instagram video/reel information.
    Encourages (COI), (DRY), (KISS), (YAGNI), (CCAC), (SRP), (OCP), (LSP), (ISP), (DIP).
    """

    @staticmethod
    def parse_iso8601_duration(duration: str) -> Optional[float]:
        """
        parse_iso8601_duration converts an ISO 8601 duration string to total seconds.

        :param [duration]: Duration in ISO 8601 format (e.g. "PT0H0M18.100S").
        :return: Float value of duration in seconds or None if parsing fails.
        """
        pattern = re.compile(
            r"^PT" r"(?:(\d+)H)?" r"(?:(\d+)M)?" r"(?:(\d+(?:\.\d+)?)S)?$"
        )
        match = pattern.match(duration)
        if not match:
            return None

        try:
            hours_str, minutes_str, seconds_str = match.groups()
            hours = int(hours_str) if hours_str else 0
            minutes = int(minutes_str) if minutes_str else 0
            seconds = float(seconds_str) if seconds_str else 0.0
            return hours * 3600 + minutes * 60 + seconds
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_video_duration(node: Dict) -> Optional[float]:
        """
        get_video_duration extracts total video duration from XML dash manifest.

        :param [node]: Dictionary containing dash_info with 'video_dash_manifest' key.
        :return: Float value of duration in seconds or None if extraction fails.
        """
        try:
            xml_string = node.get("dash_info", {}).get("video_dash_manifest")
            root = ET.fromstring(xml_string)
            duration_str = root.attrib.get("mediaPresentationDuration")
            return Extractor.parse_iso8601_duration(duration_str)
        except (ET.ParseError, ValueError, TypeError):
            return None

    @staticmethod
    def extract_video_info(node: Dict) -> Optional[Dict]:
        """
        extract_video_info obtains main video details from a media node.

        :param [node]: Media node with keys like 'is_video', 'video_url', 'dimensions', etc.
        :return: Dictionary with extracted video info or None if invalid or incomplete.
        """
        if node.get("is_video") is not True:
            return None

        video_url = node.get("video_url")
        likes = node.get("edge_media_preview_like", {}).get("count")
        comments = node.get("edge_media_to_comment", {}).get("count")
        views = node.get("video_view_count")
        posted_time = node.get("taken_at_timestamp")
        width = node.get("dimensions", {}).get("width")
        height = node.get("dimensions", {}).get("height")
        shortcode = node.get("shortcode")

        # Convert values to integers when possible
        try:
            likes = int(likes)
            comments = int(comments)
            views = int(views)
            posted_time = int(posted_time)
            width = int(width)
            height = int(height)
        except (ValueError, TypeError):
            return None

        duration = Extractor.get_video_duration(node)
        if duration is None or width <= 0 or height <= 0 or not shortcode:
            return None

        return {
            "url": video_url,
            "shortcode": shortcode,
            "likes": likes,
            "comments": comments,
            "views": views,
            "posted_time": posted_time,
            "video_duration": duration,
            "dimensions": {
                "width": width,
                "height": height,
            },
        }

    def extract_reel_info(self, media: Dict) -> Optional[Dict]:
        """
        extract_reel_info obtains reel details from an Instagram media object.

        :param [media]: Dictionary with reel data (e.g. 'code', 'like_count', 'play_count', etc.).
        :return: Dictionary with reel info or None if invalid or incomplete.
        """
        if not media:
            return None

        required_keys = {
            "code": str,
            "like_count": (int, float),
            "comment_count": (int, float),
            "play_count": (int, float),
            "taken_at": (int, float),
            "video_duration": (int, float),
            "original_width": (int, float),
            "original_height": (int, float),
            "number_of_qualities": (int, float),
        }

        extracted = {}
        for key, expected_type in required_keys.items():
            value = media.get(key)
            if value is None or not isinstance(value, expected_type):
                return None
            extracted[key] = value

        owner = media.get("owner")
        if not owner or "username" not in owner:
            return None

        reel_url = f"https://www.instagram.com/reel/{extracted['code']}"
        return {
            "url": reel_url,
            "shortcode": extracted["code"],
            "username": owner["username"],
            "likes": extracted["like_count"],
            "comments": extracted["comment_count"],
            "views": extracted["play_count"],
            "posted_time": extracted["taken_at"],
            "video_duration": extracted["video_duration"],
            "numbers_of_qualities": extracted["number_of_qualities"],
            "dimensions": {
                "width": extracted["original_width"],
                "height": extracted["original_height"],
            },
        }

import re
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, Union


class Extractor:
    """
    Extractor provides utility methods to parse Instagram video/reel information.

    Utilizes composition by calling helper functions for various parsing tasks.
    """

    @staticmethod
    def parse_iso8601_duration(duration: str) -> Optional[float]:
        """
        Convert ISO 8601 duration string to total seconds.

        **Parameters:**
        - `[duration]`: ISO 8601 duration string (e.g. "PT0H0M18.100S").

        **Returns:**
        - Float representing total seconds if successful, otherwise None.
        """
        pattern: re.Pattern = re.compile(
            r"^PT"  # Duration begins with PT
            r"(?:(\d+)H)?"  # Optional hours group
            r"(?:(\d+)M)?"  # Optional minutes group
            r"(?:(\d+(?:\.\d+)?)S)?"  # Optional seconds group, supports decimals
            r"$"
        )
        match = pattern.match(duration)
        if not match:
            return None

        try:
            hours_str, minutes_str, seconds_str = match.groups()
            hours: int = int(hours_str) if hours_str else 0
            minutes: int = int(minutes_str) if minutes_str else 0
            seconds: float = float(seconds_str) if seconds_str else 0.0
            return hours * 3600 + minutes * 60 + seconds
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_video_duration(node: Dict[str, Any]) -> Optional[float]:
        """
        Extract total video duration from XML DASH manifest.

        **Parameters:**
        - `[node]`: Dictionary with key 'dash_info' containing 'video_dash_manifest'.

        **Returns:**
        - Float representing duration in seconds if extraction is successful, otherwise None.
        """
        try:
            xml_string: Optional[str] = node.get("dash_info", {}).get(
                "video_dash_manifest"
            )
            if not xml_string:
                return None
            root: ET.Element = ET.fromstring(xml_string)
            duration_str: Optional[str] = root.attrib.get("mediaPresentationDuration")
            return (
                Extractor.parse_iso8601_duration(duration_str) if duration_str else None
            )
        except (ET.ParseError, ValueError, TypeError):
            return None

    @staticmethod
    def extract_video_info(
        node: Dict[str, Any]
    ) -> Optional[Dict[str, Union[int, float, str, Dict[str, int]]]]:
        """
        Obtain main video details from a media node.

        **Parameters:**
        - `[node]`: Dictionary representing media with keys like 'is_video', 'video_url', 'taken_at_timestamp',
          'dimensions', and 'shortcode'.

        **Returns:**
        - Dictionary with extracted video info if valid, otherwise None.
        """
        if node.get("is_video") is not True:
            return None

        # Ensure required keys exist and are valid
        video_url: Optional[str] = node.get("video_url")
        posted_time_raw: Any = node.get("taken_at_timestamp")
        shortcode: Optional[str] = node.get("shortcode")
        dimensions_node: Dict[str, Any] = node.get("dimensions", {})

        if not (video_url and posted_time_raw and shortcode and dimensions_node):
            return None

        try:
            posted_time: int = int(posted_time_raw)
            # Return None if posted_time is invalid
            if posted_time <= 0:
                return None

            likes: int = int(node.get("edge_media_preview_like", {}).get("count", 0))
            comments: int = int(node.get("edge_media_to_comment", {}).get("count", 0))
            views: int = int(node.get("video_view_count", 0))
            width: int = int(dimensions_node.get("width", 0))
            height: int = int(dimensions_node.get("height", 0))
        except (ValueError, TypeError):
            return None

        duration: Optional[float] = Extractor.get_video_duration(node)
        if duration is None or width <= 0 or height <= 0:
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

    def extract_reel_info(
        self, media: Dict[str, Any]
    ) -> Optional[Dict[str, Union[str, int, float, Dict[str, int]]]]:
        """
        Obtain reel details from an Instagram media object.

        **Parameters:**
        - `[media]`: Dictionary with reel data keys such as 'code', 'like_count', 'comment_count',
          'play_count', 'taken_at', 'video_duration', 'original_width', 'original_height',
          and 'number_of_qualities'.

        **Returns:**
        - Dictionary with extracted reel information if valid, otherwise None.
        """
        if not media:
            return None

        required_keys: Dict[str, Any] = {
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

        extracted: Dict[str, Union[int, float, str]] = {}
        for key, expected_type in required_keys.items():
            value: Any = media.get(key)
            if value is None or not isinstance(value, expected_type):
                return None
            extracted[key] = value

        owner: Optional[Dict[str, Any]] = media.get("owner")
        if not owner or "username" not in owner:
            return None

        reel_url: str = f"https://www.instagram.com/reel/{extracted['code']}"
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

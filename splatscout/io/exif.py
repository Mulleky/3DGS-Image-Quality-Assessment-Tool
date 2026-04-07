"""EXIF extraction helpers."""

from __future__ import annotations

from typing import Any

from PIL import ExifTags, Image

GPS_TAGS = ExifTags.GPSTAGS
TAG_NAMES = ExifTags.TAGS


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, tuple) and len(value) == 2:
            numerator, denominator = value
            if denominator == 0:
                return None
            return float(numerator) / float(denominator)
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _gps_to_decimal(values: Any, ref: str | None) -> float | None:
    if not values or len(values) != 3:
        return None
    degrees = _to_float(values[0])
    minutes = _to_float(values[1])
    seconds = _to_float(values[2])
    if None in {degrees, minutes, seconds}:
        return None
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in {"S", "W"}:
        decimal *= -1
    return decimal


def extract_exif_data(image: Image.Image) -> dict[str, Any]:
    exif = image.getexif()
    if not exif:
        return {}

    parsed: dict[str, Any] = {}
    gps_info: dict[str, Any] = {}
    for tag_id, value in exif.items():
        tag_name = TAG_NAMES.get(tag_id, str(tag_id))
        if tag_name == "GPSInfo" and isinstance(value, dict):
            for gps_tag, gps_value in value.items():
                gps_info[GPS_TAGS.get(gps_tag, str(gps_tag))] = gps_value
            continue
        parsed[tag_name] = value

    gps_latitude = _gps_to_decimal(
        gps_info.get("GPSLatitude"),
        gps_info.get("GPSLatitudeRef"),
    )
    gps_longitude = _gps_to_decimal(
        gps_info.get("GPSLongitude"),
        gps_info.get("GPSLongitudeRef"),
    )

    focal_length = _to_float(parsed.get("FocalLength"))

    summary = {
        "make": parsed.get("Make"),
        "model": parsed.get("Model"),
        "focal_length_mm": focal_length,
        "gps_latitude": gps_latitude,
        "gps_longitude": gps_longitude,
    }

    return {key: value for key, value in summary.items() if value is not None}

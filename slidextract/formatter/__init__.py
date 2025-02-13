from __future__ import annotations

from slidextract.formatter import date, number
from slidextract.formatter.models import UnsupportedFormat, FormatSection

GENERAL_FORMAT = "General"


def parse_format(format_str: str) -> list[FormatSection] | GENERAL_FORMAT:
    if format_str == GENERAL_FORMAT:
        return format_str
    elif date.is_date_format(format_str):
        return date.parse_format(format_str)
    if number.is_number_format(format_str):
        return number.parse_format(format_str)
    else:
        raise UnsupportedFormat("The format string is not a date or number format.")


def apply_format(
    value: int | float | str, formats: str | list[FormatSection]
) -> str | None:
    if value is None:
        return None

    format_type_check_str = formats[0].raw if isinstance(formats, list) else formats
    if format_type_check_str == GENERAL_FORMAT:
        return str(value)
    elif date.is_date_format(format_type_check_str):
        return date.apply_format(value, format_type_check_str)
    if number.is_number_format(format_type_check_str):
        return number.apply_format(value, format_type_check_str)
    else:
        raise UnsupportedFormat("The format string is not a date or number format.")


__all__ = ["apply_format", "parse_format", "models"]

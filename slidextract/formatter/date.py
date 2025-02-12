from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Callable, TypeAlias

from typing_extensions import overload

from slidextract.core.logging import get_logger
from slidextract.formatter import common
from slidextract.formatter.models import (
    FormatSection,
    FormatSections,
    SectionPart,
    SectionPartType,
    UnsupportedFormat,
)

_logger = get_logger(__name__)

DATE_PATTERN = r"\b(yyyy|yy|mmmm|mmm|mm?m?m?|dddd|ddd|dd?|hh?|ss?(?:\.0*)?)\b"
AMPM_TIME_PATTERN = r"\bAM?\/PM?\b"

TimeFormatMapper: TypeAlias = dict[
    SectionPartType, dict[str, str | Callable[[datetime], str]]
]

FORMAT_MAPPER = TimeFormatMapper(
    {
        SectionPartType.TIME: {
            "yyyy": "%Y",
            "yy": "%y",
            "dd": "%d",
            "d": "%-d",
            "hh": "%H",
            "h": "%-H",
            "ss": "%S",
            "s": "%-S",
        },
        SectionPartType.MONTH_TIME: {
            "mmmmm": lambda dt, _: dt.strftime("%b")[0],
            "mmmm": "%B",
            "mmm": "%b",
            "mm": "%m",
            "m": "%-m",
        },
        SectionPartType.MINUTE_TIME: {
            "mm": "%M",
            "m": "%-M",
        },
        SectionPartType.AMPM_TIME: {
            "hh": "%I",
            "h": "%-I",
            "AM/PM": "%p",
            "A/P": lambda dt, _: dt.strftime("%p")[0],
        },
        SectionPartType.ELAPSE_TIME: {
            "[hh]": lambda _, days: f"{int(days * 24):02d}",  # Total hours, zero-padded
            "[h]": lambda _, days: f"{int(days * 24)}",  # Total hours, no zero-padding
            "[mm]": lambda _, days: f"{int(days * 1440) % 60:02d}",  # Total minutes, zero-padded
            "[m]": lambda _, days: f"{int(days * 1440) % 60}",  # Total minutes, no zero-padding
            "[ss]": lambda _, days: f"{int(days * 86400) % 60:02d}",  # Total seconds, zero-padded
            "[s]": lambda _, days: f"{int(days * 86400) % 60}",  # Total seconds, no zero-padding
        },
    }
)


def _remove_quotes(section: FormatSection):
    temp_container: list[SectionPart] = []

    while section.parts:
        part = section.parts.popleft()
        if part.type == SectionPartType.TEXT:
            temp_container.append(
                SectionPart(type=SectionPartType.TEXT, value=part.value.strip('"'))
            )
        else:
            temp_container.append(part)

    section.parts.extend(temp_container)


def _merge_elapse_parts(section: FormatSection):
    elapse_time_count: int = 0
    temp_container: list[SectionPart] = []

    while section.parts:
        part = section.parts.popleft()
        if part.value[-1] != "[":
            temp_container.append(part)
            continue

        if len(section.parts) < 2:
            raise UnsupportedFormat("Cannot interpret elapse time")

        open_square_bracket_part = part

        time_part: SectionPart = section.parts.popleft()
        if time_part.type != SectionPartType.TIME or not re.search(
            r"\b(hh?|mm?|ss?)\b", time_part.value
        ):
            raise UnsupportedFormat("Cannot interpret elapse time")

        close_square_bracket_part = section.parts.popleft()
        if close_square_bracket_part.value[0] != "]":
            raise UnsupportedFormat("Cannot interpret elapse time")

        open_square_bracket_left_value = open_square_bracket_part.value[:-1]
        close_square_bracket_right_value = close_square_bracket_part.value[1:]

        if len(open_square_bracket_left_value) > 0:
            temp_container.append(
                SectionPart(
                    type=SectionPartType.RAW,
                    value=open_square_bracket_left_value,
                )
            )

        temp_container.append(
            SectionPart(
                type=SectionPartType.ELAPSE_TIME,
                value=f"[{time_part.value}]",
            )
        )

        if len(close_square_bracket_right_value) > 0:
            temp_container.append(
                SectionPart(
                    type=SectionPartType.RAW,
                    value=close_square_bracket_right_value,
                )
            )

        elapse_time_count += 1

    if elapse_time_count > 1:
        raise UnsupportedFormat("One section cannot have more than one elapse time")

    section.parts.extend(temp_container)


def _determine_hour_parts(section: FormatSection):
    if all(part.type != SectionPartType.AMPM_TIME for part in section.parts):
        return

    temp_container: list[SectionPart] = []

    while section.parts:
        part = section.parts.popleft()
        if part.type == SectionPartType.TIME and re.search(r"\bh{1,2}\b", part.value):
            temp_container.append(SectionPart(SectionPartType.AMPM_TIME, part.value))
        else:
            temp_container.append(part)

    section.parts.extend(temp_container)


def _determine_month_and_minute_parts(section: FormatSection):
    temp_container: list[SectionPart] = []

    while section.parts:
        part = section.parts.popleft()
        if part.type != SectionPartType.TIME or not re.search(
            r"\bmm?m?m?m?\b", part.value
        ):
            temp_container.append(part)
            continue

        prev_time_part = next(
            (p for p in reversed(temp_container) if p.type == SectionPartType.TIME),
            None,
        )

        next_time_part = next(
            (p for p in section.parts if p.type == SectionPartType.TIME), None
        )

        m_time_part_type = (
            SectionPartType.MINUTE_TIME
            if len(part.value) in (1, 2)
            and (
                (prev_time_part and re.search(r"\b(h+|s+)\b", prev_time_part.value))
                or (next_time_part and re.search(r"\b(h+|s+)\b", next_time_part.value))
            )
            else SectionPartType.MONTH_TIME
        )

        temp_container.append(SectionPart(m_time_part_type, part.value))

    section.parts.extend(temp_container)


def _finalize_date_parts(section: FormatSection):
    temp_container: list[SectionPart] = []

    prev_part_type = SectionPartType.SPACE

    while section.parts:
        part = section.parts.popleft()
        part_type = part.type

        if part_type == SectionPartType.RAW:
            if prev_part_type == SectionPartType.RAW:
                raise UnsupportedFormat("Cannot interpret a date format")
            part_type = SectionPartType.TEXT

        prev_part_type = part_type
        temp_container.append(SectionPart(part_type, part.value))

    section.parts.extend(temp_container)


def is_date_format(format_str: str | None) -> bool:
    """Checks if the format string is a date format.

    Args:
        format_str (str | None): The format string to check.

    Returns:
        bool: True if the format string is a date format, False otherwise.
    """

    if format_str is None:
        return False

    return bool(re.search(DATE_PATTERN, format_str))


def parse_format(sections: str | list[str]) -> FormatSections:
    """Parses the format string into its respective sections.

    Args:
        sections (list[str]): The format string to parse.

    Returns:
        FormatSections: The parsed format sections.
    """

    if isinstance(sections, str):
        sections = sections.split(";")

    if len(sections) > 1:
        _logger.debug(f"Date format has more than one section. ({len(sections)})")

        raise UnsupportedFormat(
            "In the case of date format, it should have a single section."
        )

    section = FormatSection(raw=sections[0])
    section.parts.append(SectionPart(type=SectionPartType.RAW, value=sections[0]))

    common.parse_parts(section, r"\s+", SectionPartType.SPACE)
    common.parse_parts(section, common.QUOTE_PATTERN, SectionPartType.TEXT)
    _remove_quotes(section)

    common.parse_parts(section, DATE_PATTERN, SectionPartType.TIME)
    _merge_elapse_parts(section)
    common.parse_parts(section, AMPM_TIME_PATTERN, SectionPartType.AMPM_TIME)
    _determine_month_and_minute_parts(section)
    _determine_hour_parts(section)

    _finalize_date_parts(section)

    return FormatSections([section])


@overload
def apply_format(value: int | float, formats: FormatSections) -> str:
    ...


@overload
def apply_format(value: int | float, formats: str | list[str]) -> str:
    ...


def _convert_format(value: datetime, days: float, format_section: FormatSection) -> str:
    buffer: list[str] = []

    for part in format_section.parts:
        if part.type in FORMAT_MAPPER and part.value in FORMAT_MAPPER[part.type]:
            mapper = FORMAT_MAPPER[part.type]
            format_str = mapper.get(part.value, part.value)
            buffer.append(
                format_str if isinstance(format_str, str) else format_str(value, days)
            )
        elif part.type == SectionPartType.TIME and "ss." in part.value:
            decimal_places = len(part.value.split(".")[1])
            whole_seconds = value.strftime("%S")
            fractional_seconds = f"{(days * 86400) % 1:.{decimal_places}f}"[2:]
            buffer.append(f"{whole_seconds}.{fractional_seconds}")
        elif part.type == SectionPartType.ELAPSE_TIME and (
            "[ss]." in part.value or "[s]." in part.value
        ):
            decimal_places = len(part.value.split(".")[1])
            whole_seconds = int(days * 86400) % 60
            fractional_seconds = f"{(days * 86400) % 1:.{decimal_places}f}"[2:]
            buffer.append(f"{whole_seconds}.{fractional_seconds}")
        elif part.type not in SectionPartType.time_types():
            buffer.append(part.value)

    return "".join(buffer)


def apply_format(value: int | float, formats: str | list[str] | FormatSections) -> str:
    EXECL_EPOCH = datetime(1899, 12, 30)

    if not isinstance(formats, list):
        formats: FormatSections = parse_format(formats)

    date_format = formats[0]
    date_value = EXECL_EPOCH + timedelta(days=value)

    python_format = _convert_format(date_value, value, date_format)
    return date_value.strftime(python_format)


__all__ = [
    "apply_format",
    "is_date_format",
    "parse_format",
]

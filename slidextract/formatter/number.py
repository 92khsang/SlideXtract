from __future__ import annotations

import math
import re
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from slidextract.core.logging import get_logger
from slidextract.formatter import common
from slidextract.formatter.models import (
    FormatSection,
    SectionPart,
    SectionPartType,
    UnsupportedFormat,
)

_logger = get_logger(__name__)

NUMBER_SEARCH_PATTERN = r"(?<![\"'])[#0@]+(?![\"'])"
NUMBER_PATTERN = r"(?<![\"'])[#0]+(?![\"'])"
DELETE_PART_PATTERNS = [r"\[\b.*\b\]", r"\*."]
UNDERSCORE_PATTERN = r"_."

UNIQUE_PART_TYPES: list[SectionPartType] = [
    SectionPartType.PERCENTAGE,
    SectionPartType.DOT,
    SectionPartType.FRACTION,
    SectionPartType.EXPONENT,
    SectionPartType.NUMBER_TEXT,
]

NO_COEXIST_PART_TYPES: list[SectionPartType] = [
    SectionPartType.PERCENTAGE,
    SectionPartType.FRACTION,
    SectionPartType.EXPONENT,
    SectionPartType.NUMBER_TEXT,
]

SECTION_SPECIFIC_PART_TYPES: dict[SectionPartType, set[int]] = {
    SectionPartType.PERCENTAGE: {0},
    SectionPartType.FRACTION: {0},
    SectionPartType.EXPONENT: {0},
    SectionPartType.NUMBER_TEXT: {0, 3},
}


@dataclass
class NumberFormatSection(FormatSection):
    index: int
    counts: dict[SectionPartType, int] = field(default_factory=dict)

    integer_number: str | None = None
    decimal_place: str | None = None
    exponent_number: str | None = None
    fraction_limit: int = 0
    divide_thousands_count: int = 0
    has_thousands_separator: bool = False

    def increase_count(self, part_type: SectionPartType, count: int = 1):
        if (
            part_type in SECTION_SPECIFIC_PART_TYPES
            and self.index not in SECTION_SPECIFIC_PART_TYPES[part_type]
        ):
            raise UnsupportedFormat(
                f"{part_type.name} parts are not allowed in this section with index {self.index}."
            )

        self.counts[part_type] = (
            self.counts[part_type] + count if part_type in self.counts else count
        )

        if self.counts[part_type] > 1 and part_type in UNIQUE_PART_TYPES:
            raise UnsupportedFormat(
                f"Multiple {part_type.name} parts detected. "
                f"Only one of each type is allowed."
            )
        elif self.no_coexisting_parts_count > 1:
            raise UnsupportedFormat(f"Multiple no-coexisting parts detected.")

    @property
    def no_coexisting_parts_count(self):
        return sum(
            count for key, count in self.counts.items() if key in NO_COEXIST_PART_TYPES
        )

    @property
    def has_percentage(self):
        return self.counts.get(SectionPartType.PERCENTAGE, 0) > 0

    @property
    def has_exponent(self):
        return self.counts.get(SectionPartType.EXPONENT, 0) > 0

    @property
    def integer_number_length(self):
        return len(self.integer_number) if self.integer_number else 0

    @property
    def integer_zero_count(self):
        return self.integer_number.count("0") if self.integer_number else 0

    @property
    def decimal_place_length(self):
        return len(self.decimal_place) if self.decimal_place else 0

    def __str__(self):
        buffer = [super().__str__(), "\ncounts: ["]

        for key, value in self.counts.items():
            buffer.append(f"{key.name}:{value}, ")
        buffer.append("]\n")

        for key, value in vars(self).items():
            if key in {"counts", "parts", "raw"}:
                continue
            buffer.append(f"{key}:{value}, ")

        buffer.append(f"has_percentage:{self.has_percentage}, ")
        buffer.append(f"has_exponent:{self.has_exponent}, ")

        return "".join(buffer)


def _is_zero_number_only_part(part: SectionPart):
    return part.type == SectionPartType.NUMBER and re.findall(r"\b0+\b", part.value)


def _search_specific_chars(section: NumberFormatSection):
    SPECIFIC_CHAR_MAP = {
        "%": SectionPartType.PERCENTAGE,
        ".": SectionPartType.DOT,
        "@": SectionPartType.NUMBER_TEXT,
    }

    # ORDER IS IMPORT
    SPECIFIC_PATTERN_MAP = {
        r",": SectionPartType.COMMA,
        r"(\?+\/\?+)": SectionPartType.FRACTION,
        r"\?+": SectionPartType.QUESTION_MARK,
        r"E[\+|\-]": SectionPartType.EXPONENT,
    }

    temp_container: list[SectionPart] = []
    while section.parts:
        part = section.parts.popleft()
        count = 0
        part_type = part.type

        current_parts: deque[SectionPart] = deque([part])

        if part_type == SectionPartType.RAW:
            if part.value in SPECIFIC_CHAR_MAP:
                part_type = SPECIFIC_CHAR_MAP[part.value]
                current_parts[-1] = SectionPart(type=part_type, value=part.value)
                count += 1
            else:
                for pattern, search_type in SPECIFIC_PATTERN_MAP.items():
                    for match in re.findall(pattern, part.value, re.IGNORECASE):
                        current_parts.append(SectionPart(type=search_type, value=match))
                        count += 1

                    if count > 0:
                        current_parts.popleft()
                        part_type = search_type
                        break

            if part_type != part.type:
                section.increase_count(part_type, count)

        temp_container.extend(current_parts)
        current_parts.clear()

    section.parts.extend(temp_container)


def _finalize_section(section: NumberFormatSection):
    temp_container: deque[SectionPart] = deque()
    merge_parts: deque[SectionPart] = deque()
    integer_number = ""

    def append_more_part(temp: deque[SectionPart]):
        temp.append(section.parts.popleft())

    def merge_all():
        new_value_buffer: list[str] = []
        while merge_parts:
            new_value_buffer.append(merge_parts.popleft().value)
            temp_container.pop()

        if new_value_buffer:
            merged_part = SectionPart(
                type=SectionPartType.NUMBER,
                value="".join(new_value_buffer),
            )
            temp_container.append(merged_part)

    while section.parts:
        part = section.parts.popleft()
        temp_parts: deque[SectionPart] = deque([part])

        prev_part = temp_container[-1] if temp_container else None
        next_part = section.parts[0] if section.parts else None

        match part.type:
            case SectionPartType.DOT:
                if any(
                    type_ != SectionPartType.NUMBER
                    for type_ in [prev_part.type, next_part.type]
                ):
                    raise UnsupportedFormat("Invalid decimal number format")
                section.decimal_place = next_part.value

                append_more_part(temp_parts)
                merge_parts.extend(temp_parts)
            case SectionPartType.EXPONENT:
                if next_part.type != SectionPartType.NUMBER:
                    raise UnsupportedFormat("Invalid exponent format")
                section.exponent_number = next_part.value

                append_more_part(temp_parts)
                merge_parts.extend(temp_parts)
            case SectionPartType.FRACTION:
                if prev_part.type != SectionPartType.SPACE:
                    raise UnsupportedFormat(
                        f"Unexpected previous section format: {prev_part.type}"
                    )

                groups = re.match(r"(\?+)/(\?+)", part.value).groups()
                if len(groups) != 2 or groups[0] != groups[1]:
                    raise UnsupportedFormat("Invalid fraction format")

                merge_parts.appendleft(temp_container[-1])  # For SPACE PART
                merge_parts.appendleft(temp_container[-2])  # For Merged Part
                merge_parts.append(part)

                section.fraction_limit = groups[0].count("?")
            case SectionPartType.COMMA:
                if prev_part.type not in {
                    SectionPartType.NUMBER,
                    SectionPartType.COMMA,
                }:
                    raise UnsupportedFormat(f"Unexpected section format: {section.raw}")

                if next_part and next_part.type == SectionPartType.NUMBER:
                    section.has_thousands_separator = True
                elif next_part is None or next_part.type == SectionPartType.COMMA:
                    section.divide_thousands_count += 1

                if section.has_thousands_separator and len(next_part.value) != 3:
                    raise UnsupportedFormat(
                        f"Unexpected next number format: {next_part.value}"
                    )

                merge_parts.append(part)
            case SectionPartType.NUMBER:
                if section.decimal_place or section.exponent_number:
                    raise UnsupportedFormat(f"Unexpected section format: {section.raw}")

                merge_parts.append(part)
                integer_number += part.value
            case _:
                if part.type == SectionPartType.RAW:
                    part = SectionPart(type=SectionPartType.TEXT, value=part.value)
                    temp_parts.popleft()
                    temp_parts.appendleft(part)
                merge_all()

        temp_container.extend(temp_parts)

    if integer_number != "":
        INTEGER_PATTERN = r"(#+0*|#*0+)"
        integer_match_str = re.search(INTEGER_PATTERN, integer_number)
        if integer_number != integer_match_str.group(0):
            raise UnsupportedFormat(f"Invalid integer number format: {integer_number}")

    section.integer_number = integer_number

    merge_all()
    section.parts.extend(temp_container)


def _format_fraction(value: float, section: NumberFormatSection) -> str:
    """Converts decimal values to mixed fractions for `# ?/?` format."""

    import fractions

    fraction_value = fractions.Fraction(value).limit_denominator(
        10**section.fraction_limit
    )
    whole_part = fraction_value.numerator // fraction_value.denominator
    remainder = fraction_value.numerator % fraction_value.denominator

    output = f"{whole_part} " if whole_part != 0 else ""
    output += (
        f"{remainder}/{fraction_value.denominator}"
        if remainder != 0
        else ("" * section.fraction_limit * 2)
    )

    return output


def _format_exponent(num: float, section: NumberFormatSection) -> str:
    exponent = (
        math.floor(math.log10(abs(num)) / section.integer_number_length)
        * section.integer_number_length
        if num != 0
        else 0
    )
    coefficient = num / (10**exponent)

    coefficient_str = f"{coefficient:.{section.decimal_place_length}f}"

    formatted = f"{coefficient_str}E{exponent:+d}"

    matches = re.match(r"(.*)E([+|-])(\d*)", formatted)
    return f"{matches.group(1)}E{matches.group(2)}{int(matches.group(3)):0{section.decimal_place_length}}"


def _convert_number(value: int | float, section: NumberFormatSection) -> str:
    if isinstance(value, int) and section.decimal_place:
        value = float(value)

    if section.divide_thousands_count > 0:
        value /= 1000**section.divide_thousands_count

    if section.has_percentage:
        value *= 100
    elif section.has_exponent:
        return _format_exponent(value, section)
    elif section.fraction_limit > 0:
        return _format_fraction(value, section)

    number_format = (
        f",.{section.decimal_place_length}f"
        if section.has_thousands_separator
        else f".{section.decimal_place_length}f"
    )
    return f"{value:{number_format}}"


def _convert_value(value: int | float | str, section: NumberFormatSection) -> list[str]:
    FORMAT_MAPPER: dict[
        SectionPartType, Callable[[int | float | str, SectionPart], str]
    ] = {
        SectionPartType.NUMBER_TEXT: lambda v, _: f"{v}",
        SectionPartType.QUESTION_MARK: lambda _, p: " " * len(part.value),
        SectionPartType.NUMBER: lambda v, _: _convert_number(v, section),
    }

    buffer: list[str] = []

    for part in section.parts:
        if part.type in FORMAT_MAPPER:
            buffer.append(FORMAT_MAPPER[part.type](value, part))
        else:
            buffer.append(part.value)

    return buffer


def is_number_format(format_str: str | None) -> bool:
    """Checks if the format string is a number format.

    Args:
        format_str (str | None): The format string to check.

    Returns:
        bool: True if the format string is a date format, False otherwise.
    """

    if format_str is None:
        return False

    return bool(re.search(NUMBER_SEARCH_PATTERN, format_str))


def parse_format(format_str: str) -> list[NumberFormatSection]:
    """Parses the format string into its respective sections.

    Args:
        format_str (str): The format string to parse.

    Returns:
        list[NumberFormatSection]: The parsed format sections.
    """
    sections = format_str.split(";")

    if any(not is_number_format(section) for section in sections[:2]):
        raise UnsupportedFormat("The format string is not a number format.")

    format_sections = [
        NumberFormatSection(
            index=idx,
            raw=section,
            parts=deque([SectionPart(type=SectionPartType.RAW, value=section)]),
        )
        for idx, section in enumerate(sections)
    ]

    for section in format_sections:
        common.replace_value_in_parts(section, DELETE_PART_PATTERNS, "")
        common.replace_value_in_parts(section, UNDERSCORE_PATTERN, " ")

        common.parse_parts(section, r"\s+", SectionPartType.SPACE)
        common.parse_parts(section, common.QUOTE_PATTERN, SectionPartType.TEXT)
        common.remove_quotes(section)

        common.parse_parts(section, NUMBER_PATTERN, SectionPartType.NUMBER)
        _search_specific_chars(section)

        _finalize_section(section)

        if sum(1 for part in section.parts if part.type == SectionPartType.NUMBER) > 1:
            raise UnsupportedFormat(
                f"Only one number is allowed in section {section.raw}."
            )

    return format_sections


def apply_format(
    value: int | float | str, formats: str | list[NumberFormatSection]
) -> str:
    sections: list[NumberFormatSection] = (
        parse_format(formats) if isinstance(formats, str) else formats
    )

    section_count = len(sections)
    if isinstance(value, str):
        buffer = _convert_value(value, sections[3 if section_count > 3 else 0])
    elif int(value) == 0 and section_count > 2:
        buffer = _convert_value(value, sections[2])
    elif value < 0 and section_count > 1:
        buffer = _convert_value(abs(value), sections[1])
    else:
        buffer = _convert_value(value, sections[0])

    return "".join(buffer)

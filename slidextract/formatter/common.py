from __future__ import annotations

import re

from slidextract.formatter import utils
from slidextract.formatter.models import FormatSection, SectionPartType, SectionPart

QUOTE_PATTERN = r'"([^"]+)"'


def parse_parts(
    section: FormatSection,
    pattern: str,
    match_part_type: SectionPartType,
    parse_part_types: list[SectionPartType] | None = None,
    flags: int = re.NOFLAG,
):
    """
    Splits the format string into its respective sections.

    Args:
        section (FormatSection): The section to be parsed.
        pattern (str): The pattern to split the section by.
        match_part_type (SectionPartType): The type of the part if matched.
        parse_part_types (list[SectionPartType], optional): The types of parts to be parsed. Defaults to None.
        flags (int, optional): The flags to use when splitting the section. Defaults to re.NOFLAG.

    Returns:
        None
    """

    if parse_part_types is None:
        parse_part_types = [SectionPartType.RAW]

    temp_container: list[SectionPart] = []

    while section.parts:
        part = section.parts.popleft()
        if part.type not in parse_part_types:
            temp_container.append(part)
            continue

        split_parts = utils.split(part.value, pattern, flags)

        for part, is_match in split_parts:
            part_type = SectionPartType.RAW
            if is_match:
                part_type = match_part_type

            temp_container.append(SectionPart(type=part_type, value=part))

    section.parts.extend(temp_container)


def remove_quotes(section: FormatSection):
    """
    Removes double quotes from the beginning and end of the TEXT part of a format section.

    Args:
        section (FormatSection): The format section to remove quotes from.

    Returns:
        None
    """
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


def replace_value_in_parts(
    section: FormatSection,
    patterns: str | list[str],
    replace_str: str,
    part_types: SectionPartType | list[SectionPartType] = SectionPartType.RAW,
):
    """
    Replaces parts of the format section with the given replacement string.

    Args:
        section (FormatSection): The format section to replace parts in.
        patterns (str | list[str]): The patterns to replace.
        replace_str (str): The string to replace the matched parts with.
        part_types (SectionPartType | list[SectionPartType], optional): The types of parts to replace. Defaults to SectionPartType.RAW.

    Returns:
        None
    """
    if not isinstance(part_types, list):
        part_types = [part_types]

    if not isinstance(patterns, list):
        patterns = [patterns]

    temp_container: list[SectionPart] = []

    while section.parts:
        part = section.parts.popleft()
        if part.type in part_types:
            part_value = part.value
            for replace_pattern in patterns:
                for replace_part in re.findall(replace_pattern, part_value):
                    part_value = part_value.replace(replace_part, replace_str)
            part = SectionPart(type=part.type, value=part_value)
        temp_container.append(part)
    section.parts.extend(temp_container)


__all__ = {"QUOTE_PATTERN", "parse_parts", "remove_quotes", "replace_value_in_parts"}

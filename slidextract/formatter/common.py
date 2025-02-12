from __future__ import annotations

import re

from slidextract.formatter import utils
from slidextract.formatter.models import FormatSection, SectionPartType, SectionPart

QUOTE_PATTERN = r'"([^"]+)"'


def parse_parts(
    section: FormatSection,
    pattern: str,
    match_part_type: SectionPartType,
    flags: int = re.NOFLAG,
):
    """
    Splits the format string into its respective sections.

    Args:
        section (FormatSection): The section to be parsed.
        pattern (str): The pattern to split the section by.
        match_part_type (SectionPartType): The type of the part if matched.
        flags (int, optional): The flags to use when splitting the section. Defaults to re.NOFLAG.

    Returns:
        None
    """

    temp_container: list[SectionPart] = []

    while section.parts:
        part = section.parts.popleft()
        if part.type != SectionPartType.RAW:
            temp_container.append(part)
            continue

        split_parts = utils.split(part.value, pattern, flags)

        for part, is_match in split_parts:
            part_type = SectionPartType.RAW
            if is_match:
                part_type = match_part_type

            temp_container.append(SectionPart(type=part_type, value=part))

    section.parts.extend(temp_container)


__all__ = {
    "QUOTE_PATTERN",
    "parse_parts",
}

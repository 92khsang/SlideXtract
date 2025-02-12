from __future__ import annotations

import re
from collections import deque


def split(text: str, pattern: str, flags: int = re.NOFLAG) -> deque[tuple[str, bool]]:
    """
    Splits the text into chunks based on the given pattern.

    Args:
        text: The text to split.
        pattern: The pattern to match.
        flags: The regex flags.

    Returns:
        A deque containing tuples of (chunk, is_match).
    """

    result = deque()
    last_end = 0

    for match in re.finditer(pattern, text, flags=flags):
        start, end = match.span()

        if last_end != start:
            chunk = text[last_end:start]
            if chunk:
                result.append((chunk, False))

        matched_text = text[start:end]
        if matched_text:
            result.append((matched_text, True))

        last_end = end

    if last_end < len(text):
        remaining_text = text[last_end:]
        if remaining_text:
            result.append((remaining_text, False))

    return result

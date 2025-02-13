from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import TypeAlias


class UnsupportedFormat(BaseException):
    pass


class SectionPartType(str, Enum):
    """
    The type of section part.

    Attributes:
        RAW: Not processed
        SPACE: Space (= )
        TEXT: Text
        NUMBER: Number (e.g., 0.00, #,##)
        TIME: Time (e.g., yyyy, mm, dd, hh, ss)
        AMPM_TIME: AM/PM
        ELAPSE_TIME: Elapsed time (e.g., [hh], [mm], [ss])
        EXPONENT: Exponent (e.g., 0.00E+00)
        PERCENTAGE: Percentage (=%)
        COMMA: Comma (= \",\")
        DOT: Dot (= .)
        UNDERSCORE: Underscore (=_)
        QUESTION_MARK: Question mark (=?)
        FRACTION: Fraction (= ?/?)
        NUMBER_TEXT: Number text
    """

    RAW = auto()
    SPACE = auto()
    TEXT = auto()
    NUMBER = auto()
    TIME = auto()
    MONTH_TIME = auto()
    MINUTE_TIME = auto()
    AMPM_TIME = auto()
    ELAPSE_TIME = auto()
    EXPONENT = auto()
    PERCENTAGE = auto()
    COMMA = auto()
    DOT = auto()
    UNDERSCORE = auto()
    QUESTION_MARK = auto()
    FRACTION = auto()
    NUMBER_TEXT = auto()

    @classmethod
    def time_types(cls):
        return [
            cls.TIME,
            cls.MONTH_TIME,
            cls.MINUTE_TIME,
            cls.ELAPSE_TIME,
            cls.AMPM_TIME,
        ]


@dataclass(frozen=True, slots=True)
class SectionPart:
    """
    A part of a format section.

    Attributes:
        type: The type of the part.
        value: The value of the part.
    """

    type: SectionPartType
    value: str

    def __str__(self):
        return f'{self.type.name}: "{self.value}"'


@dataclass
class FormatSection:
    """
    A section of a format string.

    Attributes:
        raw: The raw format string of this section.
        parts: A list of parts in this section.
    """

    raw: str
    parts: deque[SectionPart]

    def __str__(self):
        return f"raw: '{self.raw}', parts: {[str(part) for part in self.parts]}"


FormatSections: TypeAlias = list[FormatSection]

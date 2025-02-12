from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
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
        TIME: Time (e.g., yyyy, mm, dd, hh, ss)
        AMPM_TIME: AM/PM
        ELAPSE_TIME: Elapsed time (e.g., [hh], [mm], [ss])
        SCIENTIFIC: Scientific notation (e.g., 0.00E+00)
        PERCENTAGE: Percentage (=%)
        COMMA: Comma (= \",\")
        UNDERSCORE: Underscore (=_)
        QUESTION_MARK: Question mark (=?)
        ASTERISK: Asterisk (=*)
    """

    RAW = auto()
    SPACE = auto()
    TEXT = auto()
    TIME = auto()
    MONTH_TIME = auto()
    MINUTE_TIME = auto()
    AMPM_TIME = auto()
    ELAPSE_TIME = auto()
    SCIENTIFIC = auto()
    PERCENTAGE = auto()
    COMMA = auto()
    UNDERSCORE = auto()
    QUESTION_MARK = auto()
    ASTERISK = auto()

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
    raw: str
    parts: deque[SectionPart] = field(default_factory=deque)

    def __str__(self):
        return f"raw: {self.raw}, parts: {[str(part) for part in self.parts]}"


FormatSections: TypeAlias = list[FormatSection]

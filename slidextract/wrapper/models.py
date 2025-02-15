from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BBox:
    """
    Represents a bounding box for shapes.

    Attributes:
        x1: left coordinate
        y1: top coordinate
        x2: right coordinate
        y2: bottom coordinate
    """

    x1: int
    y1: int
    x2: int
    y2: int

    @classmethod
    def from_shape(cls, left: int, top: int, width: int, height: int) -> BBox:
        return cls(left, top, left + width, top + height)

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

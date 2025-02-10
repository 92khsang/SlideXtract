from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from slidextract.core.logging import get_logger
from slidextract.wrapper.models import SlideSize
from slidextract.wrapper.shape import ShapeWrapper, ShapeFilter

if TYPE_CHECKING:
    from logging import Logger

    from pptx.slide import Slide


@dataclass(frozen=True, slots=True)
class SlideFilter:
    """
    Filter conditions for extracting slides

    Attributes:
        min_shapes: minimum number of shapes in a slide
        shape_filter: filter conditions for extracting shapes
    """

    min_shapes: int = field(default=0)
    shape_filter: ShapeFilter = field(default_factory=ShapeFilter)


@dataclass(frozen=True, slots=True)
class SlideWrapper:
    """
    Wrapper for python-pptx Slide

    Attributes:
        slide: Original slide
        number: Number of the slide
        size: Size of the slide
        filter: Filter conditions for extracting shape
        shapes: List of extracted shapes
        valid: Whether the slide is valid
    """

    slide: Slide
    number: int
    size: SlideSize
    filter: SlideFilter

    shapes: list[ShapeWrapper] = field(init=False)
    valid: bool = field(init=False)

    _logger: Logger = field(default_factory=lambda: get_logger(__name__))

    def __post_init__(self):

        object.__setattr__(
            self,
            "shapes",
            [
                ShapeWrapper(shape, self.size, self.filter.shape_filter)
                for shape in self.slide.shapes
            ],
        )
        object.__setattr__(self, "valid", self._validate())

    def __getattr__(self, item):
        return getattr(self.slide, item)

    def _validate(self) -> bool:
        return self.total_shapes >= self.filter.min_shapes

    @property
    def total_shapes(self) -> int:
        return len(self.shapes)

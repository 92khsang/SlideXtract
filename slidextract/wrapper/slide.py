from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from slidextract.wrapper.models import SlideSize
from slidextract.wrapper.shape import ShapeWrapper, ShapeFilter

if TYPE_CHECKING:
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
        slide_size: Size of the slide
        slide_filter: Filter conditions for extracting shape
        shapes: List of extracted shapes
        valid: Whether the slide is valid
    """

    slide: Slide
    slide_size: SlideSize
    slide_filter: SlideFilter

    shapes: list[ShapeWrapper] = field(init=False)
    valid: bool = field(init=False)

    def __post_init__(self):
        object.__setattr__(
            self,
            "shapes",
            [
                ShapeWrapper(shape, self.slide_size, self.slide_filter.shape_filter)
                for shape in self.slide.shapes
            ],
        )
        object.__setattr__(self, "valid", self._validate())

    def _validate(self) -> bool:
        return self.total_shapes >= self.slide_filter.min_shapes

    @property
    def total_shapes(self) -> int:
        return len(self.shapes)

from __future__ import annotations

import weakref
from _weakref import ProxyType
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from slidextract.core.logging import get_logger
from slidextract.wrapper.shape import ShapeWrapper, ShapeFilter

if TYPE_CHECKING:
    from logging import Logger

    from pptx.slide import Slide
    from slidextract.wrapper import PresentationWrapper


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


@dataclass(frozen=True)
class SlideWrapper:
    """
    Wrapper for python-pptx Slide

    Attributes:
        slide: Original slide
        number: Number of the slide
        slide_filter: Filter conditions for extracting shape
        shapes: List of extracted shapes
        valid: Whether the slide is valid
    """

    slide: Slide
    number: int
    slide_filter: SlideFilter
    _presentation_proxy: weakref.ProxyType[PresentationWrapper]

    shapes: list[ShapeWrapper] = field(init=False)
    valid: bool = field(init=False)

    _logger: Logger = field(init=False)

    def __init__(
        self,
        slide: Slide,
        number: int,
        slide_filter: SlideFilter,
        _presentation_proxy: weakref.ProxyType[PresentationWrapper],
    ):
        object.__setattr__(self, "slide", slide)
        object.__setattr__(self, "number", number)
        object.__setattr__(self, "slide_filter", slide_filter)
        object.__setattr__(self, "_presentation_proxy", _presentation_proxy)

        object.__setattr__(
            self,
            "shapes",
            [
                ShapeWrapper(
                    shape,
                    self.slide_filter.shape_filter,
                    _slide_proxy=weakref.proxy(self),
                )
                for shape in self.slide.shapes
            ],
        )
        object.__setattr__(self, "valid", self._validate())
        object.__setattr__(self, "_logger", get_logger(__name__))

    def __getattr__(self, item):
        return getattr(self.slide, item)

    def _validate(self) -> bool:
        return self.total_shapes >= self.slide_filter.min_shapes

    @property
    def total_shapes(self) -> int:
        return len(self.shapes)

    @property
    def presentation(self) -> ProxyType[PresentationWrapper]:
        return self._presentation_proxy

from __future__ import annotations

from dataclasses import dataclass, field

from pptx.slide import Slide

from .models import SlideSize


@dataclass(frozen=True, slots=True)
class SlideFilter:
    pass


@dataclass(frozen=True, slots=True)
class SlideWrapper:
    slide: Slide
    slide_size: SlideSize
    slide_filter: SlideFilter

    valid: bool = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "valid", self._validate())

    def _validate(self) -> bool:
        return True

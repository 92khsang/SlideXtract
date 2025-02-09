from __future__ import annotations

from dataclasses import dataclass, field

from pptx import Presentation

from slidextract.wrapper.models import SlideSize
from slidextract.wrapper.slide import SlideWrapper, SlideFilter


@dataclass(frozen=True, slots=True)
class PresentationWrapper:
    pptx_path: str
    slide_filter: SlideFilter

    presentation: Presentation = field(init=False)
    slides: list[SlideWrapper] = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "presentation", Presentation(self.pptx_path))
        object.__setattr__(
            self,
            "slides",
            [
                SlideWrapper(
                    slide,
                    self.presentation.slides.index(slide) + 1,
                    SlideSize(self.width, self.height),
                    self.slide_filter,
                )
                for slide in self.presentation.slides
            ],
        )

    @property
    def width(self) -> int:
        return self.presentation.slide_width

    @property
    def height(self) -> int:
        return self.presentation.slide_height

    @property
    def total_slides(self) -> int:
        return len(self.slides)

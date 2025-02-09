from __future__ import annotations

from dataclasses import dataclass, field

from pptx import Presentation

from slidextract.utils import emu_to_pixels


@dataclass(frozen=True, slots=True)
class PresentationWrapper:
    pptx_path: str

    presentation: Presentation = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "presentation", Presentation(self.pptx_path))

    @property
    def width(self) -> float:
        return emu_to_pixels(self.presentation.slide_width)

    @property
    def height(self) -> float:
        return emu_to_pixels(self.presentation.slide_height)

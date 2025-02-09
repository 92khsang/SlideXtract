from __future__ import annotations

EMU_TO_PIXELS = 9525


def emu_to_pixels(emu: int) -> float:
    return emu / EMU_TO_PIXELS


def pixels_to_emu(pixels: float) -> int:
    return int(pixels * EMU_TO_PIXELS)

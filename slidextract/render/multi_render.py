from __future__ import annotations

import asyncio
import os
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
from tqdm.asyncio import tqdm
from typing_extensions import NamedTuple

from slidextract.concurrency.thread_pool import TaskMultiThreador
from slidextract.core.logging import get_logger
from slidextract.render.shape_render import render_table, render_chart
from slidextract.wrapper import PresentationWrapper
from slidextract.wrapper.slide import SlideFilter

if TYPE_CHECKING:
    from slidextract.wrapper import SlideWrapper

_logger = get_logger(__name__)


class RenderShape(NamedTuple):
    index: int
    shape_type: str
    html_str: str


def render_slide(slide: SlideWrapper, output_dir: Path):
    shape_processors = {
        "table": lambda s: render_table(s.table),
        "chart": lambda s: render_chart(s.chart),
    }

    def create_filename(shape_type_: str, shape_index: int) -> str:
        return f"{slide.presentation.pptx_path.stem}-{slide.number:04d}-{shape_type_}-{shape_index:02d}.html"

    async def _write_shape_to_file(path: Path, content: str):
        try:
            async with aiofiles.open(path, "w", encoding="utf-8") as f:
                await f.write(content)

            _logger.debug(f"Successfully wrote {path.name}")
        except Exception as ex:
            _logger.error(f"Error writing shape to file {path.name}: {ex}")

    shape_indices = defaultdict(int)
    tasks = []

    for shape in slide.shapes:
        for shape_type, processor in shape_processors.items():
            if getattr(shape, shape_type):
                try:
                    index = shape_indices[shape_type]
                    shape_indices[shape_type] += 1

                    file_name = create_filename(shape_type, index)
                    html_str = shape_processors[shape_type](shape)
                    file_path = output_dir / file_name

                    tasks.append(_write_shape_to_file(file_path, html_str))

                except Exception as e:
                    _logger.error(
                        f"Error processing shape {shape_type} in slide {slide.number}: {e}"
                    )

    if tasks:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(asyncio.gather(*tasks))
        loop.close()


async def _async_render_slides(
    slides: list[SlideWrapper], output_dir: Path, max_workers: int
):
    """Manages to render slides asynchronously using TaskMultiThreador with semaphore."""
    if not slides:
        return

    async with asyncio.Semaphore(max_workers):
        async with TaskMultiThreador(max_workers) as threador:
            async for result in threador.process_tasks(
                iter(slides),
                lambda slide: render_slide(slide, output_dir),
                batch_size=max_workers,
            ):
                pass


async def _async_render_presentation(
    presentation: PresentationWrapper,
    parent_output_dir: Path,
    max_workers: int,
    pbar: tqdm | None,
):
    """Renders all slides in a presentation."""
    output_dir = parent_output_dir / presentation.pptx_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    try:

        await _async_render_slides(presentation.slides, output_dir, max_workers)
    except Exception as e:
        _logger.error(f"Rendering failed for {presentation.pptx_path.stem}: {e}")

    finally:
        if pbar:
            pbar.update(1)


async def _async_render_presentations(
    files: set[Path],
    output_dir: Path,
    slide_filter: SlideFilter,
    max_workers: int,
    show_progress: bool,
):
    """Asynchronously processes multiple presentations with a semaphore limit."""
    pbar = (
        tqdm(total=len(files), desc="Extracting Files", unit="file", dynamic_ncols=True)
        if show_progress
        else None
    )

    tasks = [
        asyncio.create_task(
            _async_render_presentation(
                PresentationWrapper(file, slide_filter), output_dir, max_workers, pbar
            )
        )
        for file in files
    ]

    await asyncio.gather(*tasks)

    if pbar:
        pbar.close()


def render_presentations(
    source_dir: str | Path,
    output_dir: str | Path,
    slide_filter: SlideFilter | None = None,
    max_workers: int | None = None,
    show_progress: bool = False,
):
    """Entry point to process PowerPoint presentations and extract slide data."""

    source_dir = Path(source_dir)
    output_dir = Path(output_dir)

    if slide_filter is None:
        slide_filter = SlideFilter()

    if max_workers is None:
        max_workers = max(1, os.cpu_count() // 3)

    if not source_dir.is_dir():
        raise ValueError("The source directory does not exist.")

    if output_dir.exists():
        raise ValueError("Output directory already exists. Please delete it first.")

    output_dir.mkdir(parents=True)

    files: set[Path] = {file for file in source_dir.rglob("*.pptx")}

    if not files:
        _logger.info("No .pptx files found in the source directory.")
        return

    asyncio.run(
        _async_render_presentations(
            files, output_dir, slide_filter, max_workers, show_progress
        )
    )

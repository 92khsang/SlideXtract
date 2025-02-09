from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slidextract.wrapper.table import TableWrapper


def render_table(table: TableWrapper, include_style: bool = False) -> str:
    """
    Render a python-pptx Table as an HTML string.

    Args:
        table: The python-pptx Table to render.
        include_style: Whether to include the table style in the rendered HTML.

    Returns:
        str: The rendered table as an HTML string.
    """
    html = (
        [
            "<style>",
            "table { border-collapse: collapse; width: 100%; }",
            "td, th { border: 1px solid #ddd; padding: 8px; text-align: center; }",
            "</style>",
            "<table>",
        ]
        if include_style
        else ["<table>"]
    )

    num_rows = len(table.rows)
    num_cols = len(table.columns)

    rowspan_info: dict = {}
    colspan_info: dict = {}
    spanned_cells = {}

    # Pre-process spans
    for row_idx in range(num_rows):
        for col_idx in range(num_cols):
            cell = table.cell(row_idx, col_idx)
            if cell.is_spanned:
                spanned_cells[(row_idx, col_idx)] = True
            elif cell.is_merge_origin:
                rowspan = cell.span_height
                colspan = cell.span_width
                if rowspan > 1:
                    rowspan_info[(row_idx, col_idx)] = rowspan
                if colspan > 1:
                    colspan_info[(row_idx, col_idx)] = colspan
                for r in range(rowspan):
                    for c in range(colspan):
                        if r != 0 or c != 0:
                            spanned_cells[(row_idx + r, col_idx + c)] = True

    # Generate HTML table
    for row_idx in range(num_rows):
        html.append("<tr>")
        col_idx = 0

        while col_idx < num_cols:
            if (row_idx, col_idx) in spanned_cells:
                col_idx += 1
                continue

            cell = table.cell(row_idx, col_idx)
            cell_text = cell.text.replace("\n", "<br>")
            attrs = []

            if (row_idx, col_idx) in rowspan_info:
                attrs.append(f'rowspan="{rowspan_info[(row_idx, col_idx)]}"')
            if (row_idx, col_idx) in colspan_info:
                attrs.append(f'colspan="{colspan_info[(row_idx, col_idx)]}"')

            html.append(f'<td {" ".join(attrs)}>{cell_text}</td>')
            col_idx += colspan_info.get((row_idx, col_idx), 1)

        html.append("</tr>")

    html.append("</table>")
    return "\n".join(html)

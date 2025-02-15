from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Literal

from slidextract.formatter import apply_format, parse_format

if TYPE_CHECKING:
    from slidextract.wrapper import TableWrapper, ChartWrapper


def _wrap_html(buffer: deque[str], tag: str, *, attributes: str | None = None) -> None:
    buffer.appendleft(f"<{tag}{' ' + attributes if attributes else ''}>")
    buffer.append(f"</{tag}>")


def _build_table(
    values: list[list[str]],
    h_headers: list[str] | None = None,
    v_headers: list[str] | None = None,
) -> deque[deque[str]]:

    table: deque[deque[str]] = deque()

    if h_headers:
        table.append(deque(h_headers))

    for value in values:
        table.append(deque(value))

    if v_headers:
        v_headers.insert(0, "")
        for index, v_header in enumerate(v_headers):
            table[index].appendleft(v_header)

    return table


def _build_table_html(
    table: deque[deque[str]],
    table_attributes: str | None = None,
) -> deque[str]:

    table_html: deque[str] = deque()

    while table:
        row = table.popleft()
        row_html = deque()
        while row:
            cell_html = deque([row.popleft()])
            _wrap_html(cell_html, "td")
            row_html.extend(cell_html)
        _wrap_html(row_html, "tr")
        table_html.extend(row_html)

    _wrap_html(table_html, "tbody")
    _wrap_html(table_html, "table", attributes=table_attributes)

    return table_html


def render_table(table: TableWrapper, *, include_style: bool = False) -> str:
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


def render_chart(
    chart: ChartWrapper,
    *,
    include_meta: bool = True,
    apply_number_format: bool = True,
    category_orientation: Literal["horizontal", "vertical"] = "vertical",
) -> str:
    """
    Render a python-pptx Chart as an HTML string.

    Args:
        chart: The python-pptx Chart to render.
        include_meta: Whether to include the chart's metadata in the rendered HTML.
        apply_number_format: Whether to apply the chart's number format to the rendered values.
        category_orientation: The orientation of the chart's category axis.

    Returns:
        str: The rendered chart as an HTML string.
    """
    buffer: deque[str] = deque()

    if len(chart.plots) == 0 or not chart.supported:
        buffer.append("Unsupported chart type")
        _wrap_html(buffer, "div", attributes="id='chart-container' state='unsupported'")
        return "\n".join(buffer)

    chart_type = chart.chart_type.name

    x_axis = chart.category_axis if "BAR" not in chart_type else chart.value_axis
    y_axis = chart.value_axis if "BAR" not in chart_type else chart.category_axis

    chart_title = chart.chart_title.text_frame.text if chart.has_title else ""
    x_title = x_axis.axis_title.text_frame.text if x_axis.has_title else ""
    y_title = y_axis.axis_title.text_frame.text if y_axis.has_title else ""

    value_format = (
        y_axis.tick_labels.number_format if apply_number_format else "General"
    )

    plot = chart.plots[0]

    categories = plot.categories
    series_collection = plot.series
    if len(series_collection) == 0:
        return ""

    category_labels: list[str] = (
        [category.label for category in categories]
        if len(categories.flattened_labels) != 0
        else [""] * len(series_collection[0].values)
    )

    title_table = _build_table(
        h_headers=["title", "xtitle", "ytitle"],
        values=[[chart_title, x_title, y_title]],
    )
    title_table_html = _build_table_html(title_table)
    buffer.extend(title_table_html)
    buffer.append("<br>")

    series_names: list[str] = []
    values: list[list[str]] = []

    sections = parse_format(value_format)
    for plot in chart.plots:
        for series in plot.series:
            series_names.append(series.name)
            row = [apply_format(v if v else 0, sections) for v in series.values]
            values.append(row)

    h_headers = (
        category_labels if category_orientation == "horizontal" else series_names
    )
    v_headers = (
        series_names if category_orientation == "horizontal" else category_labels
    )

    if category_orientation == "vertical":
        values = [list(row) for row in zip(*values)]

    main_table = _build_table(
        h_headers=h_headers,
        v_headers=v_headers,
        values=values,
    )
    main_table_html = _build_table_html(main_table, table_attributes="id='chart'")
    buffer.extend(main_table_html)

    if include_meta:
        buffer.append("<br>")
        meta_table = _build_table(
            h_headers=["ChartType", "ValueFormat"],
            values=[[chart_type, value_format]],
        )
        meta_table_html = _build_table_html(meta_table)
        buffer.extend(meta_table_html)

    _wrap_html(buffer, "div", attributes="id='chart-container'")
    return "\n".join(buffer)

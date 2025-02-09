from __future__ import annotations

from dataclasses import dataclass

from pptx.table import Table


@dataclass(frozen=True, slots=True)
class TableWrapper:
    """
    Wrapper for python-pptx Table

    Attributes:
        table: Original table
    """

    table: Table

    @property
    def rows(self):
        return self.table.rows

    @property
    def columns(self):
        return self.table.columns

    def cell(self, row_idx: int, col_idx: int):
        return self.table.cell(row_idx, col_idx)

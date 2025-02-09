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

    def __getattr__(self, name):
        return getattr(self.table, name)

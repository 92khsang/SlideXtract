from __future__ import annotations

from dataclasses import dataclass, field

from pptx.chart.chart import Chart


@dataclass(frozen=True, slots=True)
class ChartWrapper:
    """
    Wrapper for python-pptx Chart

    Attributes:
        chart: Original chart
    """

    chart: Chart
    supported: bool = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "supported", self._is_chart_supported())

    def __getattr__(self, name):
        return getattr(self.chart, name)

    def _is_chart_supported(self):
        try:
            _ = self.chart.chart_type  # Try accessing chart_type
            return True
        except ValueError:
            return False

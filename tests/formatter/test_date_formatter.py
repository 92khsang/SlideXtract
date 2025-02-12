from collections import deque
from typing import List, Tuple

import pytest

from slidextract.formatter import date
from slidextract.formatter.models import FormatSection, SectionPart, SectionPartType


class DateFormatTestData:
    """
    A comprehensive collection of test cases for date format testing.
    Centralizes test data and makes it easier to maintain and extend.
    """

    VALID_DATE_FORMATS = [
        "yyyy-mm-dd",
        "dd-mmm-yy",
        "dd-mmm",
        "mmm-yy",
        "h:mm AM/PM",
        "h:mm:ss AM/PM",
        "h:mm",
        "h:mm:ss",
        "yyyy-mm-dd h:mm",
        "mm:ss",
        "mm:ss.0",
        "[h]:mm:ss",
        "mm-dd-yy",
        'yyyy"년" mm"월" dd"일"',
        'h"시" mm"분"',
        'h"시" mm"분" ss"초"',
        'yyyy"年" mm"月" dd"日"',
        "mm-dd",
        "yyyy/mm/dd",
        'mm"월" dd"일"',
    ]

    PARSE_FORMATS = [
        (
            "yyyy-mm-dd",
            FormatSection(
                raw="yyyy-mm-dd",
                parts=deque(
                    [
                        SectionPart(SectionPartType.TIME, "yyyy"),
                        SectionPart(SectionPartType.TEXT, "-"),
                        SectionPart(SectionPartType.MONTH_TIME, "mm"),
                        SectionPart(SectionPartType.TEXT, "-"),
                        SectionPart(SectionPartType.TIME, "dd"),
                    ]
                ),
            ),
        ),
        (
            "dd-mmm-yy",
            FormatSection(
                raw="dd-mmm-yy",
                parts=deque(
                    [
                        SectionPart(SectionPartType.TIME, "dd"),
                        SectionPart(SectionPartType.TEXT, "-"),
                        SectionPart(SectionPartType.MONTH_TIME, "mmm"),
                        SectionPart(SectionPartType.TEXT, "-"),
                        SectionPart(SectionPartType.TIME, "yy"),
                    ]
                ),
            ),
        ),
        (
            "h:mm AM/PM",
            FormatSection(
                raw="h:mm AM/PM",
                parts=deque(
                    [
                        SectionPart(SectionPartType.AMPM_TIME, "h"),
                        SectionPart(SectionPartType.TEXT, ":"),
                        SectionPart(SectionPartType.MINUTE_TIME, "mm"),
                        SectionPart(SectionPartType.SPACE, " "),
                        SectionPart(SectionPartType.AMPM_TIME, "AM/PM"),
                    ]
                ),
            ),
        ),
        (
            "[h]:mm:ss",
            FormatSection(
                raw="[h]:mm:ss",
                parts=deque(
                    [
                        SectionPart(SectionPartType.ELAPSE_TIME, "[h]"),
                        SectionPart(SectionPartType.TEXT, ":"),
                        SectionPart(SectionPartType.MINUTE_TIME, "mm"),
                        SectionPart(SectionPartType.TEXT, ":"),
                        SectionPart(SectionPartType.TIME, "ss"),
                    ]
                ),
            ),
        ),
        (
            'yyyy"년" mm"월" dd"일"',
            FormatSection(
                raw='yyyy"년" mm"월" dd"일"',
                parts=deque(
                    [
                        SectionPart(SectionPartType.TIME, "yyyy"),
                        SectionPart(SectionPartType.TEXT, "년"),
                        SectionPart(SectionPartType.SPACE, " "),
                        SectionPart(SectionPartType.MONTH_TIME, "mm"),
                        SectionPart(SectionPartType.TEXT, "월"),
                        SectionPart(SectionPartType.SPACE, " "),
                        SectionPart(SectionPartType.TIME, "dd"),
                        SectionPart(SectionPartType.TEXT, "일"),
                    ]
                ),
            ),
        ),
    ]

    CONVERT_FORMATS = [
        ("yyyy-mm-dd", "1903-05-18"),
        ("dd-mmm-yy", "18-May-03"),
        ("dd-mmm", "18-May"),
        ("mmm-yy", "May-03"),
        ("h:mm AM/PM", "1:26 PM"),
        ("h:mm:ss AM/PM", "1:26:24 PM"),
        ("h:mm", "13:26"),
        ("h:mm:ss", "13:26:24"),
        ("yyyy-mm-dd h:mm", "1903-05-18 13:26"),
        ("mm:ss", "26:24"),
        ("mm:ss.0", "26:24.0"),
        ("[h]:mm:ss", "29629:26:24"),
        ("mm-dd-yy", "05-18-03"),
        ('yyyy"년" mm"월" dd"일"', "1903년 05월 18일"),
        ('h"시" mm"분"', "13시 26분"),
        ('h"시" mm"분" ss"초"', "13시 26분 24초"),
        ('yyyy"年" mm"月" dd"日"', "1903年 05月 18日"),
        ("mm-dd", "05-18"),
        ("yyyy/mm/dd", "1903/05/18"),
        ('mm"월" dd"일"', "05월 18일"),
    ]

    @classmethod
    def get_valid_date_formats(cls) -> List[Tuple[str, bool]]:
        """
        Generate test cases for valid date formats.

        Returns:
            List of tuples containing format string and expected validation result
        """
        return [(fmt, True) for fmt in cls.VALID_DATE_FORMATS]


class TestDateFormatter:
    """
    Comprehensive test suite for date formatting functionality.
    """

    @pytest.mark.parametrize(
        "format_str, expected", DateFormatTestData.get_valid_date_formats()
    )
    def test_is_date_format(self, format_str: str, expected: bool):
        """
        Test whether various format strings are correctly identified as date formats.

        Args:
            format_str (str): The format string to test
            expected (bool): Expected result of format validation
        """
        assert (
            date.is_date_format(format_str) == expected
        ), f"Failed to validate date format: {format_str}"

    @pytest.mark.parametrize(
        "format_str, format_section", DateFormatTestData.PARSE_FORMATS
    )
    def test_parse_format(self, format_str: str, format_section: FormatSection):
        """
        Test parsing of different date format strings.

        Args:
            format_str (str): The format string to parse
            format_section (FormatSection): Expected parsed result
        """
        parsed_section = date.parse_format(format_str)[0]
        assert (
            parsed_section == format_section
        ), f"Parsing failed for format: {format_str}"

    @pytest.mark.parametrize(
        "format_str, expected_output", DateFormatTestData.CONVERT_FORMATS
    )
    def test_apply_format(self, format_str: str, expected_output: str):
        """
        Test conversion of numeric values to formatted date strings.

        Args:
            format_str (str): The format to apply
            expected_output (str): Expected formatted output
        """
        assert (
            date.apply_format(1234.56, format_str) == expected_output
        ), f"Format conversion failed for: {format_str}"


class TestDateFormatterPerformance:
    """
    Performance and coverage tests for date formatting.
    """

    def test_performance(self):
        """
        Basic performance test to ensure reasonable execution time.
        """
        import timeit

        def test_multiple_formats():
            for fmt in DateFormatTestData.VALID_DATE_FORMATS:
                date.apply_format(1234.56, fmt)

        execution_time = timeit.timeit(test_multiple_formats, number=100)
        assert (
            execution_time < 1.0
        ), f"Performance test failed. Execution time: {execution_time}"

    def test_coverage(self):
        """
        Verify that all defined formats are processed.
        """
        processed_formats = set()
        for fmt in DateFormatTestData.VALID_DATE_FORMATS:
            try:
                result = date.apply_format(1234.56, fmt)
                processed_formats.add(fmt)
            except Exception as e:
                pytest.fail(f"Format {fmt} failed: {e}")

        assert len(processed_formats) == len(
            DateFormatTestData.VALID_DATE_FORMATS
        ), "Not all formats were successfully processed"

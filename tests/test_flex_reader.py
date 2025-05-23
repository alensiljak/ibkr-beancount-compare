'''
Tests for flex_reader
'''

import os
from src.flex_reader import get_latest_filename, load_report
from src.model import FlexQueryResponse


def test_parse_file(cmp_params):
    """
    Test function to parse a file
    """
    report = load_report(cmp_params.flex_report_path, cmp_params.flex_reports_dir)
    actual = FlexQueryResponse().from_xml_content(report)

    assert len(actual.flex_statements.flex_statement.cash_transactions) > 0


def test_dir_list():
    """
    Test function to test the directory listing
    """
    actual = get_latest_filename("tests/*.xml")
    assert actual
    expected = os.path.join("tests", "tcf.xml")
    assert actual == expected

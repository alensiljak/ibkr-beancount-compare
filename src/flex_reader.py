"""
Read the required Flex Query report file(s).
The logic for choosing a file.
"""

import os
import glob
import logging
from typing import Optional

FILE_SUFFIX = "_cash-tx.xml"


def load_report(
    flex_report_path: Optional[str] = None, flex_reports_dir: Optional[str] = None
) -> str:
    """
    Loads the Flex report.
    If the direct path to the report is given, then the report is loaded. This
    parameter takes precedence over path.
    If the path to the directory is given, the latest report from that directory
    will be loaded.
    """
    logging.debug("load_report with: %s, %s", flex_report_path, flex_reports_dir)

    if flex_report_path:
        report_path = flex_report_path
    elif flex_reports_dir:
        report_path = get_latest_report_path(flex_reports_dir)
    else:
        raise ValueError("Either flex_report_path or flex_reports_dir must be provided")

    logging.info("Using report: %s", report_path)

    with open(report_path, "r", encoding="utf-8") as file:
        return file.read()


def get_latest_report_path(report_dir: str) -> str:
    """
    Gets the path to the latest report file in the given directory or the
    current directory, if None received.
    """
    pattern = f"*{FILE_SUFFIX}"

    if report_dir:
        pattern = os.path.join(report_dir, pattern)

    return get_latest_filename(pattern)


def get_latest_filename(file_pattern: str) -> str:
    """
    Get the latest of the files matching the given pattern.
    Pattern example: *.xml
    """
    logging.debug(f"file pattern: {file_pattern}")

    files = glob.glob(file_pattern)
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {file_pattern}")

    latest_file = max(files, key=os.path.getctime)
    return latest_file

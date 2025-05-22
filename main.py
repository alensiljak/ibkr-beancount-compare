#!/usr/bin/env python3
"""
IBKR - Beancount comparer
Compares the IB Flex report to the transactions in Ledger/Beancount,
displaying the missing ones.
"""

import argparse
import sys
from datetime import date, timedelta

from pathlib import Path
from typing import Optional

from loguru import logger
from pydantic import ValidationError

from model import (
    CommonTransaction,
    CompareParams,
    FlexQueryResponse,
    IbCashTransaction,
    SymbolMetadata,
)
from ibflex_reader import get_ib_tx_py

# Constants
TRANSACTION_DAYS: int = 60
ISO_DATE_FORMAT_STR: str = "%Y-%m-%d"


def main():
    """The main program entry"""
    parser = argparse.ArgumentParser(
        description="Compares IB Flex report transactions to Ledger/Beancount and displays missing ones."
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-f",
        "--flex-report-path",
        type=str,
        help="Path to a specific IB Flex Report XML file.",
    )
    group.add_argument(
        "-d",
        "--flex-reports-dir",
        type=str,
        help="Path to a directory containing IB Flex Report XML files (latest .xml will be used).",
    )

    parser.add_argument(
        "-l",
        "--ledger-journal-file",
        type=str,
        required=True,
        help="Path to the Ledger/Beancount journal file.",
    )
    parser.add_argument(
        "-s",
        "--symbols-path",
        type=str,
        required=True,
        help="Path to the symbols mapping CSV file.",
    )
    parser.add_argument(
        "-e",
        "--effective-dates",
        action="store_true",
        help="Use effective dates for comparison instead of report dates.",
    )

    args = parser.parse_args()

    params = CompareParams(
        flex_report_path=args.flex_report_path,
        flex_reports_dir=args.flex_reports_dir,
        ledger_journal_file=args.ledger_journal_file,
        symbols_path=args.symbols_path,
        effective_dates=args.effective_dates,
    )

    result_message = compare_py(params)

    if result_message and result_message.startswith("Error:"):
        # Errors are already logged by logger in compare_py
        print(f"\n{result_message.strip()}", file=sys.stderr)
        sys.exit(1)


# --- Enums and Helper Functions (equivalent to flex_enums) ---


# --- Stub/Helper functions for external dependencies ---


def get_ledger_start_date_py(days_ago: Optional[int] = None) -> str:
    """
    Stub for ledger_runner::get_ledger_start_date.
    Calculates the start date for fetching ledger transactions.
    """
    num_days = days_ago if days_ago is not None else TRANSACTION_DAYS
    start_date_obj = date.today() - timedelta(days=num_days)
    return start_date_obj.strftime(ISO_DATE_FORMAT_STR)


def get_ledger_tx_py(
    ledger_journal_file: Optional[str],
    start_date_str: str,
    use_effective_date: bool,  # Parameter from Rust, might influence ledger query
) -> list[CommonTransaction]:
    """
    Stub for ledger_runner::get_ledger_tx.
    Fetches transactions from Ledger.
    This would involve running `ledger print` or similar and parsing output.
    """
    logger.debug(
        f"Stub: Called get_ledger_tx_py with journal: {ledger_journal_file}, "
        f"start_date: {start_date_str}, effective_dates: {use_effective_date}"
    )
    # Example: Return an empty list or dummy data for testing
    # if ledger_journal_file and Path(ledger_journal_file).exists():
    #     # Actual implementation would parse the ledger file
    #     pass
    return []


# --- Core Logic Functions ---


def get_comparison_date_py(
    common_tx: CommonTransaction, use_effective_date: bool
) -> str:
    """Determines the date string to use for comparison based on the flag."""
    if use_effective_date:
        return common_tx.date.strftime(ISO_DATE_FORMAT_STR)
    else:
        # common_tx.report_date is already "YYYY-MM-DD" string
        return common_tx.report_date


def get_oldest_ib_date_py(
    ib_common_txs: list[CommonTransaction], use_effective_date: bool
) -> str:
    """Finds the oldest transaction date in the IB report to time-box Ledger query."""
    if not ib_common_txs:
        return get_ledger_start_date_py(None)  # Use default days

    try:
        # min() will raise ValueError if ib_common_txs is empty, but we check above.
        oldest_tx = min(
            ib_common_txs, key=lambda tx: get_comparison_date_py(tx, use_effective_date)
        )
    except ValueError:  # Should not happen due to the check, but as a safeguard
        logger.warning(
            "Could not determine oldest IB date from an empty list post-check."
        )
        return get_ledger_start_date_py(None)

    logger.debug(f"Oldest IB common transaction (for ledger range): {oldest_tx}")
    return get_comparison_date_py(oldest_tx, use_effective_date)


def compare_txs_py(
    ib_common_txs: list[CommonTransaction],
    ledger_common_txs: list[CommonTransaction],
    use_effective_date: bool,
) -> str:
    """Compares IB transactions against Ledger transactions and identifies new ones."""
    result_output_lines: list[str] = []

    for ibtx in ib_common_txs:
        logger.debug(f"Searching for matches for IB tx: {ibtx}")
        # logging.debug(f"Available ledger_txs: {ledger_common_txs}") # Can be very verbose

        ib_comparison_date_str = get_comparison_date_py(ibtx, use_effective_date)
        logger.debug(f"Using IB date for comparison: {ib_comparison_date_str}")

        found_match = False
        for ledger_tx in ledger_common_txs:
            # Ledger transaction's date for comparison.
            # Assuming ledger_tx.date is the primary date for matching.
            ledger_tx_date_str = ledger_tx.date.strftime(ISO_DATE_FORMAT_STR)

            # Amount comparison: ledger amount is typically opposite of IB income.
            # e.g., IB dividend is +10, Ledger entry might be Assets:Broker +10, Income:Dividends -10
            # So, ledger_tx.amount == -ibtx.amount if ledger represents income as negative.
            # The Rust code has: tx.amount == ibtx.amount.mul(Decimal::NEGATIVE_ONE)
            # This means ledger_tx.amount == -ibtx.amount
            if (
                ledger_tx_date_str == ib_comparison_date_str
                and ledger_tx.symbol == ibtx.symbol
                and ledger_tx.amount == -ibtx.amount  # Decimal comparison
                and ledger_tx.currency == ibtx.currency
                and ledger_tx.type == ibtx.type
            ):  # 'type' is the descriptive string
                logger.debug(f"Found match for IB tx {ibtx} -> Ledger tx {ledger_tx}")
                found_match = True
                break  # Assuming one match is sufficient

        if not found_match:
            output_line = f"New: {ibtx}\n"
            print(output_line, end="")  # Print to console immediately
            result_output_lines.append(output_line)

    print("Complete.")  # Rust: println!("Complete.")
    return "".join(result_output_lines)


def compare_py(params: CompareParams) -> str:
    """Compares transactions in the downloaded IB Flex report to Ledger."""
    logger.debug(f"Starting comparison with params: {params}")

    try:
        # get_ib_report_tx
        ib_common_txs = get_ib_tx_py(params)
        logger.info(f"Found {len(ib_common_txs)} relevant IB common transactions.")
        if not ib_common_txs:
            msg = "No new IB transactions found to process. Exiting...\n"
            print(msg, end="")
            return msg

        # Sort IB records by report_date, effective_date, symbol, type
        ib_common_txs.sort(
            key=lambda tx: (
                tx.report_date,  # String "YYYY-MM-DD"
                tx.date,  # datetime.date object
                tx.symbol,
                tx.type,
            )
        )
        logger.debug(
            f"Sorted IB common transactions: {ib_common_txs if len(ib_common_txs) < 10 else str(len(ib_common_txs)) + ' items'}"
        )

        # identify the start date for the tx range:
        start_date_for_ledger = get_oldest_ib_date_py(
            ib_common_txs, params.effective_dates
        )
        logger.info(f"Determined ledger query start date: {start_date_for_ledger}")

        # get_ledger_tx
        ledger_common_txs = get_ledger_tx_py(
            params.ledger_journal_file,
            start_date_for_ledger,
            params.effective_dates,  # Pass this flag to ledger fetching logic
        )
        logger.info(
            f"Found {len(ledger_common_txs)} Ledger common transactions for the period."
        )

        # compare
        comparison_result = compare_txs_py(
            ib_common_txs, ledger_common_txs, params.effective_dates
        )
        return comparison_result

    except FileNotFoundError as e:
        logger.error(f"File not found error during comparison: {e}")
        return f"Error: File not found - {e}\n"
    except ValueError as e:
        logger.error(f"Value error during comparison: {e}")
        return f"Error: Invalid value - {e}\n"
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return f"Error: An unexpected error occurred - {e}\n"


# --- Example Usage (similar to tests in Rust) ---
if __name__ == "__main__":
    main()

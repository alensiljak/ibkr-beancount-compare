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
def get_cash_action_string(ib_action_code: str) -> str:
    """Maps IB action codes to descriptive strings."""
    if ib_action_code == "Deposits/Withdrawals":
        return "DepositWithdraw"
    if ib_action_code == "Broker Interest Paid":
        return "BrokerIntPaid"
    if ib_action_code == "Broker Interest Received":
        return "BrokerIntRcvd"
    if ib_action_code == "Withholding Tax":
        return "WhTax"
    if ib_action_code == "Bond Interest Received":
        return "BondIntRcvd"
    if ib_action_code == "Bond Interest Paid":
        return "BondIntPaid"
    if ib_action_code == "Other Fees":
        return "Fees"
    if ib_action_code == "Dividends":
        return "Dividend"
    if ib_action_code == "Payment In Lieu Of Dividends":
        return "PaymentInLieu"
    if ib_action_code == "Commission Adjustments":
        return "CommAdj"

    raise ValueError("Unrecognized cash action type: %s", ib_action_code)


# --- Stub/Helper functions for external dependencies ---


def load_report_content_py(
    flex_report_path: Optional[str], flex_reports_dir: Optional[str]
) -> str:
    """
    Stub for flex_reader::load_report.
    Loads content from a specific report file or finds one in a directory.
    """
    file_path_to_load: Optional[Path] = None
    if flex_report_path:
        file_path_to_load = Path(flex_report_path)
    elif flex_reports_dir:
        dir_path = Path(flex_reports_dir)
        if dir_path.is_dir():
            # Example: find latest .xml file (simple version)
            xml_files = sorted(
                [f for f in dir_path.glob("*.xml") if f.is_file()],
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            if xml_files:
                file_path_to_load = xml_files[0]
                logger.info(f"Using latest report from directory: {file_path_to_load}")
            else:
                raise FileNotFoundError(f"No XML reports found in {flex_reports_dir}")
        else:
            raise NotADirectoryError(
                f"flex_reports_dir is not a directory: {flex_reports_dir}"
            )
    else:
        raise ValueError("Either flex_report_path or flex_reports_dir must be provided")

    if not file_path_to_load or not file_path_to_load.exists():
        raise FileNotFoundError(f"Report file not found: {file_path_to_load}")

    logger.info(f"Loading report from: {file_path_to_load}")
    with open(file_path_to_load, "r", encoding="utf-8") as f:
        return f.read()


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


def read_symbols_py(path: Path) -> list[SymbolMetadata]:
    """Reads a CSV file and returns a list of lists."""
    # Ensure this import is here or at the top of the file
    import csv

    data = []
    try:
        with open(path, "r", newline="", encoding="utf-8") as csvfile:
            # Use DictReader to read rows as dictionaries
            reader = csv.DictReader(csvfile)
            if reader.fieldnames:
                logger.debug(f"Symbols CSV field names: {reader.fieldnames}")
            else:  # Should not happen with a valid CSV, but good to check
                logger.warning(
                    f"Symbols CSV at {path} appears to be empty or has no header."
                )
                return []

            for row_dict in reader:
                try:
                    metadata_instance = SymbolMetadata(**row_dict)
                    data.append(metadata_instance)
                except ValidationError as ve:
                    logger.warning(
                        f"Skipping invalid row in symbols CSV {path}: {row_dict}. Error: {ve}"
                    )
    except FileNotFoundError:
        logger.error(f"Error: Symbols file not found at {path}")
        return []
    return data


# --- Core Logic Functions ---


def map_symbols_py(meta: SymbolMetadata) -> tuple[str, str]:
    """Maps SymbolMetadata to (ib_symbol, ledger_symbol) tuple."""
    ib_symbol: str
    if meta.ib_symbol:
        ib_symbol = meta.ib_symbol
    else:
        if meta.namespace is None:
            # Original Rust code panics here.
            raise ValueError(
                f"SymbolMetadata for '{meta.symbol}' is missing namespace when ib_symbol is also missing."
            )
        ib_symbol = f"{meta.namespace}:{meta.symbol}"

    ledger_symbol: str
    if meta.ledger_symbol:
        ledger_symbol = meta.ledger_symbol
    else:
        ledger_symbol = meta.symbol

    return ib_symbol, ledger_symbol


def load_symbols_py(symbols_file_path_str: str) -> dict[str, str]:
    """Loads symbol mappings from the given path."""
    logger.debug(f"Loading symbols from {symbols_file_path_str}")
    path = Path(symbols_file_path_str)
    if not path.exists():
        raise FileNotFoundError(
            f"The symbols file {symbols_file_path_str} does not exist!"
        )

    symbol_metadata_list = read_symbols_py(path)  # Uses the stubbed function

    # Resulting map is <ib_symbol_from_report, ledger_symbol_for_comparison>
    securities_map: dict[str, str] = {}
    for meta in symbol_metadata_list:
        try:
            ib_sym, ledger_sym = map_symbols_py(meta)
            securities_map[ib_sym] = ledger_sym
        except ValueError as e:
            logger.warning(f"Skipping symbol due to mapping error: {e}")
            continue

    return securities_map


def ib_cash_transaction_to_common(ib_tx: IbCashTransaction) -> CommonTransaction:
    """Converts an IbCashTransaction to a CommonTransaction."""
    return CommonTransaction(
        date=ib_tx.date_time_obj.date(),
        report_date=ib_tx.report_date_str,
        symbol=ib_tx.symbol,
        type=get_cash_action_string(ib_tx.type_code),  # Use descriptive type
        amount=ib_tx.amount,
        currency=ib_tx.currency,
        description=ib_tx.description,
    )


def convert_ib_txs_into_common_py(
    ib_tx_list: list[IbCashTransaction], symbols_path_str: str
) -> list[CommonTransaction]:
    """Converts raw IB cash transactions to CommonTransactions, applying symbol mappings."""
    try:
        symbols_map = load_symbols_py(symbols_path_str)  # <ib_symbol, ledger_symbol>
    except FileNotFoundError:
        logger.warning(
            f"Symbols file not found at {symbols_path_str}. Proceeding without symbol mapping."
        )
        symbols_map = {}

    logger.debug(
        f"Symbols loaded for conversion: {symbols_map if symbols_map else 'None'}"
    )

    common_txs: list[CommonTransaction] = []

    # Transaction types to include in the comparison
    to_include_types = ["Dividend", "WhTax", "PaymentInLieu"]
    logger.debug(f"Will include transaction types: {to_include_types}")

    for ib_tx in ib_tx_list:
        common_tx = ib_cash_transaction_to_common(ib_tx)

        logger.debug(
            f"Converting ib tx: {ib_tx.symbol} code:{ib_tx.type_code} -> common_type:{common_tx.type}"
        )

        if common_tx.type not in to_include_types:
            logger.info(
                f"Skipping transaction (type not included): {common_tx.symbol} {common_tx.type}"
            )
            # The Rust code prints "Skipped: {}", assuming __str__ for CashTransaction
            print(f"Skipped (type): {ib_tx}")
            continue

        # Apply symbol mapping: common_tx.symbol is initially the IB symbol.
        # We need to map it to the ledger symbol if a mapping exists.
        if common_tx.symbol in symbols_map:
            original_symbol = common_tx.symbol
            common_tx.symbol = symbols_map[common_tx.symbol]
            logger.debug(f"Adjusted symbol: {original_symbol} -> {common_tx.symbol}")

        common_txs.append(common_tx)

    return common_txs


def read_flex_report_py(params: CompareParams) -> list[IbCashTransaction]:
    """
    Reads and parses the Flex Report, returning a list of IB Cash Transactions.
    Sorts by date/time, symbol, type.
    """
    xml_content = load_report_content_py(
        params.flex_report_path, params.flex_reports_dir
    )
    response = FlexQueryResponse.from_xml_content(xml_content)

    # Extract transactions. The Rust code implies accessing a singular path.
    # Our Python parsing puts all relevant txs into this list.
    ib_tx_list = response.flex_statements.flex_statement.cash_transactions

    # Sort by date/time, symbol, type (raw type code from XML)
    ib_tx_list.sort(key=lambda ct: (ct.date_time_obj, ct.symbol, ct.type_code))

    return ib_tx_list


def get_ib_tx_py(params: CompareParams) -> list[CommonTransaction]:
    """
    Gets IB transactions from the Flex report and converts them to
    CommonTransactions, for comparison.
    symbols is a HashMap of symbol rewrites.
    """
    raw_ib_txs = read_flex_report_py(params)
    common_txs = convert_ib_txs_into_common_py(raw_ib_txs, params.symbols_path)
    return common_txs


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

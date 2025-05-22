"""
IBKR - Beancount comparer
Compares the IB Flex report to the transactions in Ledger/Beancount,
displaying the missing ones.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
# from enum import Enum
from pathlib import Path
from typing import Optional
from loguru import logger

from model import CommonTransaction, CompareParams, IbCashTransaction, SymbolMetadata


# Constants
TRANSACTION_DAYS: int = 60
ISO_DATE_FORMAT_STR: str = "%Y-%m-%d"


def main():
    """The main program entry"""
    # flex_report_path: params.flex_report_path.to_owned(),
    # flex_reports_dir: params.flex_reports_dir.to_owned(),
    # ledger_journal_file: params.ledger_journal_file.to_owned(),
    # symbols_path: params.symbols_path.to_owned(),
    # effective_dates: params.effective,

    print("Hello from ibkr-beancount-compare!")


def compare():
    """Compares transactions in the downloaded IB Flex report to Ledger."""
    logger.debug("comparing distributions, ")

    # todo: get_ib_report_tx

    # todo: sort IB records by dates, symbol, type

    # identify the start date for the tx range:

    # get_ledger_tx

    # compare


def get_ib_tx():
    """
    Returns transactions from the Flex Report, for comparison.
    symbols is a HashMap of symbol rewrites.
    """
    read_flex_report()
    # convert_ib_txs_into_common


def read_flex_report():
    """
    Reads the Cash Transaction records from the Flex Report.
    Sorts by date/time, symbol, type.
    """


####################################################################
#!/usr/bin/env python3


# --- Enums and Helper Functions (equivalent to flex_enums) ---
def get_cash_action_string(ib_action_code: str) -> str:
    """Maps IB action codes to descriptive strings."""
    if ib_action_code == "DIV":
        return "Dividend"
    elif ib_action_code == "WHTAX":
        return "Withholding Tax"
    elif ib_action_code == "LIEU":
        return "PaymentInLieu"
    # Add other mappings if they exist in the original flex_enums::cash_action
    return ib_action_code  # For "Other" types or unmapped


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
                logging.info(f"Using latest report from directory: {file_path_to_load}")
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

    logging.info(f"Loading report from: {file_path_to_load}")
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
    logging.debug(
        f"Stub: Called get_ledger_tx_py with journal: {ledger_journal_file}, "
        f"start_date: {start_date_str}, effective_dates: {use_effective_date}"
    )
    # Example: Return an empty list or dummy data for testing
    # if ledger_journal_file and Path(ledger_journal_file).exists():
    #     # Actual implementation would parse the ledger file
    #     pass
    return []


def read_symbols_py(path: Path) -> list[SymbolMetadata]:
    """
    Stub for as_symbols::read_symbols.
    Reads symbol metadata from a file (e.g., CSV).
    """
    logging.debug(f"Stub: Called read_symbols_py for path: {path}")
    # Example: Return dummy data for testing
    # This should parse a file like 'tests/symbols.csv'
    # if "symbols.csv" in str(path):
    #     return [
    #         SymbolMetadata(symbol="BRK.B", ib_symbol="BRK/B", ledger_symbol="BRK-B"),
    #         SymbolMetadata(symbol="MSFT", namespace="NASDAQ", ledger_symbol="MSFT"),
    #         SymbolMetadata(symbol="VBAL.TO", ib_symbol="VBAL", ledger_symbol="VBAL")
    #     ]
    return []


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
    logging.debug(f"Loading symbols from {symbols_file_path_str}")
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
            logging.warning(f"Skipping symbol due to mapping error: {e}")
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
        logging.warning(
            f"Symbols file not found at {symbols_path_str}. Proceeding without symbol mapping."
        )
        symbols_map = {}

    logging.debug(
        f"Symbols loaded for conversion: {symbols_map if symbols_map else 'None'}"
    )

    common_txs: list[CommonTransaction] = []

    # Transaction types to include in the comparison
    to_include_types = ["Dividend", "Withholding Tax", "PaymentInLieu"]
    logging.debug(f"Will include transaction types: {to_include_types}")

    for ib_tx in ib_tx_list:
        common_tx = ib_cash_transaction_to_common(ib_tx)

        logging.debug(
            f"Converting ib tx: {ib_tx.symbol} code:{ib_tx.type_code} -> common_type:{common_tx.type}"
        )

        if common_tx.type not in to_include_types:
            logging.info(
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
            logging.debug(f"Adjusted symbol: {original_symbol} -> {common_tx.symbol}")

        common_txs.append(common_tx)

    return common_txs


def read_flex_report_py(params: CompareParams) -> list[IbCashTransaction]:
    """Reads and parses the Flex Report, returning a list of IB cash transactions."""
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
    """Gets IB transactions from the Flex report and converts them to CommonTransactions."""
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
        logging.warning(
            "Could not determine oldest IB date from an empty list post-check."
        )
        return get_ledger_start_date_py(None)

    logging.debug(f"Oldest IB common transaction (for ledger range): {oldest_tx}")
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
    """Main function to compare transactions from IB Flex report to Ledger."""
    logger.debug(f"Starting comparison with params: {params}")

    try:
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

        start_date_for_ledger = get_oldest_ib_date_py(
            ib_common_txs, params.effective_dates
        )
        logger.info(f"Determined ledger query start date: {start_date_for_ledger}")

        ledger_common_txs = get_ledger_tx_py(
            params.ledger_journal_file,
            start_date_for_ledger,
            params.effective_dates,  # Pass this flag to ledger fetching logic
        )
        logger.info(
            f"Found {len(ledger_common_txs)} Ledger common transactions for the period."
        )

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
    # This section is for demonstration.
    # You'll need to create dummy files or implement the stubs for this to run.

    # Create dummy files and directories for testing
    test_dir = Path("temp_test_data")
    test_dir.mkdir(exist_ok=True)

    dummy_symbols_path = test_dir / "dummy_symbols.csv"
    with open(dummy_symbols_path, "w") as f:
        # ib_symbol,ledger_symbol,namespace,symbol_for_meta
        f.write("IB_SYM_A,LDG_SYM_A,,\n")  # Basic mapping
        f.write("IB_SYM_B,LDG_SYM_B,,\n")
        f.write(",LDG_SYM_C,NMSPC_C,SYM_C\n")  # Namespace based mapping
        f.write("XYZ.US,XYZ,,\n")  # For symbol XYZ

    dummy_flex_report_path = test_dir / "dummy_flex_report.xml"

    dummy_ledger_file_path = test_dir / "dummy_journal.ledger"

    # Override stubs for the example
    def example_read_symbols_py(path: Path) -> list[SymbolMetadata]:
        if "dummy_symbols.csv" in str(path):
            return [
                SymbolMetadata(
                    symbol="XYZ.US_meta", ib_symbol="XYZ.US", ledger_symbol="XYZ"
                ),
                SymbolMetadata(
                    symbol="SYM_C", namespace="NMSPC_C", ledger_symbol="LDG_SYM_C"
                ),
            ]
        return []

    def example_get_ledger_tx_py(
        ledger_journal_file, start_date_str, use_effective_date
    ) -> list[CommonTransaction]:
        # Simplified parsing for the example
        txs = []
        if (
            ledger_journal_file
            and Path(ledger_journal_file).name == "dummy_journal.ledger"
        ):
            # This is a very basic representation of a matched ledger transaction
            # For XYZ Dividend
            txs.append(
                CommonTransaction(
                    date=datetime.strptime("2023-10-10", "%Y-%m-%d").date(),
                    report_date="2023-10-10",  # Ledger usually has one date, using it for both
                    symbol="XYZ",  # Ledger symbol
                    type="Dividend",
                    amount=Decimal("-100.00"),  # Opposite for income
                    currency="USD",
                    description="XYZ Dividend from ledger",
                )
            )
        return txs

    # Monkey patch the stubs for this example run
    global read_symbols_py, get_ledger_tx_py
    _original_read_symbols = read_symbols_py
    _original_get_ledger_tx = get_ledger_tx_py
    read_symbols_py = example_read_symbols_py
    get_ledger_tx_py = example_get_ledger_tx_py

    print("--- Running Example Comparison ---")
    params = CompareParams(
        flex_report_path=str(dummy_flex_report_path),
        flex_reports_dir=None,
        ledger_journal_file=str(dummy_ledger_file_path),
        symbols_path=str(dummy_symbols_path),
        effective_dates=False,  # Using report date for IB comparison
    )

    result_string = compare_py(params)
    print("\n--- Comparison Result String ---")
    print(result_string)
    print("--- End of Example ---")

    # Expected output for the example:
    # New: 2023-10-05/2023-10-10 XYZ      Withholding Tax    -15.00 USD, XYZ Stock Tax
    # (The dividend should be matched, the "OTHER" type IB tx is skipped)

    # Cleanup (optional)
    # import shutil
    # shutil.rmtree(test_dir)

    # Restore original stubs if needed elsewhere
    read_symbols_py = _original_read_symbols
    get_ledger_tx_py = _original_get_ledger_tx

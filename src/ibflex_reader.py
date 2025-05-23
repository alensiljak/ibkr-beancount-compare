"""
Code for reading the IBKR Flex report
"""

from pathlib import Path
from typing import Optional
from loguru import logger
from src.flex_reader import load_report
from src.model import (
    CommonTransaction,
    CompareParams,
    FlexQueryResponse,
    IbCashTransaction,
)
from src.symbols import SymbolMetadata, read_symbols


def get_ib_tx(params: CompareParams) -> list[CommonTransaction]:
    """
    Gets IB transactions from the Flex report and converts them to
    CommonTransactions, for comparison.
    symbols is a HashMap of symbol rewrites.
    """
    raw_ib_txs = read_flex_report(params)
    common_txs = convert_ib_txs_into_common(raw_ib_txs, params.symbols_path)
    return common_txs


def read_flex_report(params: CompareParams) -> list[IbCashTransaction]:
    """
    Reads and parses the Flex Report, returning a list of IB Cash Transactions.
    Sorts by date/time, symbol, type.
    """
    xml_content = load_report(
        params.flex_report_path, params.flex_reports_dir
    )
    response = FlexQueryResponse.from_xml_content(xml_content)

    # Extract transactions. The Rust code implies accessing a singular path.
    # Our Python parsing puts all relevant txs into this list.
    ib_tx_list = response.flex_statements.flex_statement.cash_transactions

    # Sort by date/time, symbol, type (raw type code from XML)
    ib_tx_list.sort(key=lambda ct: (ct.date_time_obj, ct.symbol, ct.type_code))

    return ib_tx_list


def convert_ib_txs_into_common(
    ib_tx_list: list[IbCashTransaction], symbols_path_str: str
) -> list[CommonTransaction]:
    """Converts raw IB cash transactions to CommonTransactions, applying symbol mappings."""
    try:
        symbols_map = load_symbols(symbols_path_str)  # <ib_symbol, ledger_symbol>
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
            logger.debug(
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


def load_symbols(symbols_file_path_str: str) -> dict[str, str]:
    """Loads symbol mappings from the given path."""
    logger.debug(f"Loading symbols from {symbols_file_path_str}")
    path = Path(symbols_file_path_str)
    if not path.exists():
        raise FileNotFoundError(
            f"The symbols file {symbols_file_path_str} does not exist!"
        )

    symbol_metadata_list = read_symbols(path)  # Uses the stubbed function

    # Resulting map is <ib_symbol_from_report, ledger_symbol_for_comparison>
    securities_map: dict[str, str] = {}
    for meta in symbol_metadata_list:
        try:
            ib_sym, ledger_sym = map_symbols(meta)
            securities_map[ib_sym] = ledger_sym
        except ValueError as e:
            logger.warning(f"Skipping symbol due to mapping error: {e}")
            continue

    return securities_map


def map_symbols(meta: SymbolMetadata) -> tuple[str, str]:
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

"""
Model for the comparer.
"""

# --- Data Classes (equivalent to model and flex_query structs) ---
from dataclasses import dataclass, field
from typing import Optional
from decimal import Decimal
from datetime import date, datetime
import xml.etree.ElementTree as ET
from loguru import logger

ISO_DATE_FORMAT_STR: str = "%Y-%m-%d"


@dataclass
class IbCashTransaction:
    """Represents a CashTransaction from the IB Flex Report XML."""

    symbol: str
    description: str
    report_date_str: str  # "YYYY-MM-DD"
    date_time_obj: datetime  # Parsed from "YYYY-MM-DDTHH:MM:SS"
    amount: Decimal
    currency: str
    type_code: str  # e.g., "DIV", "WHTAX" (from XML 'type' attribute)

    def __str__(self) -> str:
        return (
            f"IbCashTx(symbol={self.symbol}, type={self.type_code}, "
            f"date={self.date_time_obj.strftime('%Y-%m-%d')}, "
            f"amount={self.amount} {self.currency})"
        )


@dataclass
class CommonTransaction:
    """A common representation for transactions from IB or Ledger."""

    date: date  # Effective date
    report_date: str  # Actual date from report, "YYYY-MM-DD"
    symbol: str
    type: str  # Descriptive type like "Dividend", "Withholding Tax"
    amount: Decimal
    currency: str
    description: str

    def __str__(self) -> str:
        """Formats the transaction for output, similar to Rust's Display impl."""
        return (
            f"{self.report_date}/{self.date.strftime(ISO_DATE_FORMAT_STR)} "
            f"{self.symbol:<6} {self.type:<8} {self.amount:>10.2f} "
            f"{self.currency}, {self.description}"
        )


@dataclass
class ParsedFlexStatement:  # Helper for parsing
    cash_transactions: list[IbCashTransaction] = field(default_factory=list)


@dataclass
class ParsedFlexStatements:  # Helper for parsing
    flex_statement: ParsedFlexStatement = field(
        default_factory=ParsedFlexStatement
    )  # Assuming one relevant statement


@dataclass
class FlexQueryResponse:
    """Represents the parsed FlexQueryResponse XML structure."""

    flex_statements: ParsedFlexStatements = field(default_factory=ParsedFlexStatements)

    @classmethod
    def from_xml_content(cls, xml_content: str) -> "FlexQueryResponse":
        """Parses XML content into a FlexQueryResponse object."""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            # Return an empty response or raise a custom error
            return cls()

        parsed_cash_txs: list[IbCashTransaction] = []

        # Simplified parsing: assumes one FlexStatement or aggregates from the first one.
        # Path: FlexQueryResponse -> FlexStatements -> FlexStatement -> 
        # CashTransactions -> CashTransaction
        first_flex_statement_elem = root.find("./FlexStatements/FlexStatement")

        if first_flex_statement_elem is not None:
            cash_transactions_elem = first_flex_statement_elem.find(
                "./CashTransactions"
            )
            if cash_transactions_elem is not None:
                for tx_elem in cash_transactions_elem.findall("./CashTransaction"):
                    try:
                        dt_str = tx_elem.get("dateTime")
                        if not dt_str:
                            raise ValueError("dateTime attribute is missing")

                        date_time_obj = (
                            datetime.strptime(dt_str, "%Y-%m-%d;%H:%M:%S")
                            if dt_str and len(dt_str) == 19
                            # length 10
                            else datetime.strptime(dt_str, ISO_DATE_FORMAT_STR)
                        )

                        report_date_str = tx_elem.get("reportDate", "")

                        amount_str = tx_elem.get("amount", "0")
                        amount_val = Decimal(amount_str)

                        tx = IbCashTransaction(
                            symbol=tx_elem.get("symbol", ""),
                            description=tx_elem.get("description", ""),
                            report_date_str=report_date_str,
                            date_time_obj=date_time_obj,
                            amount=amount_val,
                            currency=tx_elem.get("currency", ""),
                            type_code=tx_elem.get("type", ""),
                        )
                        parsed_cash_txs.append(tx)
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Skipping cash transaction due to parsing error: {e}. Element: {ET.tostring(tx_elem, encoding='unicode')}"
                        )
                        continue

        return cls(
            ParsedFlexStatements(ParsedFlexStatement(cash_transactions=parsed_cash_txs))
        )


@dataclass
class CompareParams:
    """Parameters for comparing IB Flex report and Ledger report."""

    flex_report_path: Optional[str]
    flex_reports_dir: Optional[str]
    ledger_journal_file: Optional[str]
    symbols_path: str
    effective_dates: bool

@dataclass
class SymbolMetadata:
    """Equivalent to as_symbols::SymbolMetadata"""

    # Exchange
    namespace: Optional[str]
    # Symbol at the exchange
    symbol: str
    # The currency used to express the symbol's price.
    currency: Optional[str]
    # The name of the price update provider.
    updater: Optional[str]
    # The symbol, as used by the updater.
    updater_symbol: Optional[str]
    # The symbol, as used in the Ledger journal.
    ledger_symbol: Optional[str]
    # The symbol, as used at Interactive Brokers.
    ib_symbol: Optional[str]
    # Remarks
    remarks: Optional[str]

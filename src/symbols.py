"""
Implementation of the as_symbols package.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger
from pydantic import ValidationError


@dataclass
class SymbolMetadata:
    """Equivalent to as_symbols::SymbolMetadata"""

    # Exchange
    namespace: Optional[str]
    # Symbol at the exchange
    symbol: str
    # The symbol, as used in the Ledger journal.
    ledger_symbol: Optional[str]
    # The currency used to express the symbol's price.
    currency: Optional[str]
    # The name of the price update provider.
    updater: Optional[str]
    # The symbol, as used by the updater.
    updater_symbol: Optional[str]
    # The symbol, as used at Interactive Brokers.
    ib_symbol: Optional[str]
    # Remarks
    remarks: Optional[str]

    def get_symbol(self) -> str:
        return self.ledger_symbol or self.symbol

    def symbol_w_namespace(self) -> str:
        if self.namespace:
            return f"{self.namespace}:{self.symbol}"
        return self.symbol


# def read_symbols(path: Path) -> list[SymbolMetadata]:
#     with path.open("r") as file:
#         reader = csv.DictReader(file)
#         symbols = []
#         for row in reader:
#             symbol = SymbolMetadata(
#                 symbol=row["symbol"],
#                 ledger_symbol=row.get("ledger_symbol"),
#                 namespace=row.get("namespace"),
#             )
#             symbols.append(symbol)
#         return symbols


def read_symbols(path: Path) -> list[SymbolMetadata]:
    """Reads a CSV file and returns a list of lists."""
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

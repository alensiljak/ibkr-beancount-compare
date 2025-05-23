"""
Definitions for Flex Query report
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List

from src.flex_enums import CashAction

@dataclass
class FlexStatement:
    """
    The structure of the IB Flex report statement.
    """
    report_date: datetime
    date: datetime
    type: str
    code: str
    symbol: str
    quantity: int
    amount: Decimal
    fees: Decimal
    tax: Decimal
    currency: str
    description: str

@dataclass
class FlexStatements:
    """
    The structure of the IB Flex report statements.
    """
    count: int
    statements: List[FlexStatement]

@dataclass
class FlexQueryResponse:
    """
    The structure of the IB Flex report.
    """
    flex_statements: FlexStatements

    @classmethod
    def from_string(cls, xml_string: str) -> 'FlexQueryResponse':
        """
        Parses the XML string into the FlexQueryResponse object.
        """
        # implement XML parsing logic here
        pass

@dataclass
class CashTransaction:
    """
    The structure of the IB Flex report cash transaction.
    """
    report_date: datetime
    date: datetime
    type: str
    code: str
    symbol: str
    quantity: int
    amount: Decimal
    fees: Decimal
    tax: Decimal
    currency: str
    description: str
    action: CashAction

    def __str__(self) -> str:
        return f"{self.report_date} {self.date} {self.type} {self.code} {self.symbol} {self.quantity} {self.amount} {self.fees} {self.tax} {self.currency} {self.description} {self.action}"

class CashTransactions:
    """
    The structure of the IB Flex report cash transactions.
    """
    def __init__(self, transactions: List[CashTransaction]):
        self.transactions = transactions

    def __iter__(self):
        return iter(self.transactions)

    def __len__(self):
        return len(self.transactions)

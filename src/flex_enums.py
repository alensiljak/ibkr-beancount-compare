"""
Flex Query enums
"""

from enum import Enum


class CashAction(Enum):
    DepositWithdraw = "DepositWithdraw"
    BrokerIntPaid = "BrokerIntPaid"
    BrokerIntRcvd = "BrokerIntRcvd"
    WhTax = "WhTax"
    BondIntRcvd = "BondIntRcvd"
    BondIntPaid = "BondIntPaid"
    Fees = "Fees"
    Dividend = "Dividend"
    PaymentInLieu = "PaymentInLieu"
    CommAdj = "CommAdj"


def cash_action(action: str) -> str:
    """
    Translates the IB Flex cash action name into the CashAction enum variant.
    """
    mapping = {
        "Deposits/Withdrawals": CashAction.DepositWithdraw.value,
        "Broker Interest Paid": CashAction.BrokerIntPaid.value,
        "Broker Interest Received": CashAction.BrokerIntRcvd.value,
        "Withholding Tax": CashAction.WhTax.value,
        "Bond Interest Received": CashAction.BondIntRcvd.value,
        "Bond Interest Paid": CashAction.BondIntPaid.value,
        "Other Fees": CashAction.Fees.value,
        "Dividends": CashAction.Dividend.value,
        "Payment In Lieu Of Dividends": CashAction.PaymentInLieu.value,
        "Commission Adjustments": CashAction.CommAdj.value,
    }
    return mapping.get(action, "Unknown")


def test_mapping():
    """
    Verifies that the cash_action function correctly maps the given IB
    transaction type to the corresponding CashAction enum variant.
    """
    ib_type = "Withholding Tax"
    actual = cash_action(ib_type)
    assert actual == CashAction.WhTax.value

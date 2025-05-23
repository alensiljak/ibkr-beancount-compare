"""
Test file for ledger_reg_output_parser
"""

from datetime import datetime
from decimal import Decimal
from src.ledger_reg_output_parser import (
    clean_up_register_output,
    get_row_from_register_line,
    get_rows_from_register,
)
from src.model import CommonTransaction


def test_parse_distribution_report():
    """
    Test function to parse a distribution report
    """
    ledger_output = """2022-12-15 TRET_AS Distribution                  Income:Investment:IB:TRET_AS                      -38.40 EUR           -38.40 EUR
                                          Expenses:Investment:IB:Withholding Tax              5.77 EUR           -32.63 EUR"""
    lines = ledger_output.splitlines()
    clean_lines = clean_up_register_output(lines)
    rows = get_rows_from_register(clean_lines)
    assert len(rows) == 2
    assert rows[0].symbol == "TRET_AS"
    assert rows[1].amount == Decimal("5.77")


def test_parse_posting_row():
    """
    Test function to parse a posting row
    """
    date = datetime(2022, 12, 1)
    header = CommonTransaction(
        date=date,
        payee="Supermarket",
        account="Expenses:Food",
        amount=Decimal("15"),
        currency="EUR",
    )
    line = """                                              Assets:Bank:Checking                              -15.00 EUR                    0"""
    actual = get_row_from_register_line(line, header)
    assert actual.date.year == 2022
    assert actual.report_date
    assert actual.payee == "Supermarket"
    assert actual.account == "Assets:Bank:Checking"
    assert actual.amount == Decimal("-15")
    assert actual.currency == "EUR"


def test_parse_header_row():
    """
    Test function to parse a header row
    """
    line = """2022-12-01 Supermarket                        Expenses:Food                                      15.00 EUR            15.00 EUR"""
    header = CommonTransaction()
    actual = get_row_from_register_line(line, header)
    assert actual.date.year == 2022
    assert actual.report_date
    assert actual.payee == "Supermarket"
    assert actual.account == "Expenses:Food"
    assert actual.amount == Decimal("15")
    assert actual.currency == "EUR"

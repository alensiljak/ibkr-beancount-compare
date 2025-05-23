"""
Parser for Ledger's output of the 
[register](cci:1://file:///home/alen/src/interactive-brokers-flex-rs/src/ledger_reg_output_parser.rs:40:0-57:1) command.
"""

import re
from datetime import datetime
from decimal import Decimal
from loguru import logger

from src.flex_enums import CashAction
from src.model import CommonTransaction
from src.constants import ISO_DATE_FORMAT

def clean_up_register_output(lines):
    """
    Clean-up the ledger register report.
    The report variable is a list of lines.
    """
    new_lines = []
    for line in lines:
        if line.strip() == "":
            continue
        if line[50] == " ":
            continue
        new_lines.append(line.strip())
    return new_lines

def get_rows_from_register(ledger_lines):
    """
    Parse raw lines from the ledger register output and get RegisterRow.
    """
    txs = []
    prev_row = None

    for line in ledger_lines:
        try:
            tx = get_row_from_register_line(line, prev_row)
        except Exception as e:
            logger.error(f"Error parsing ledger register output: {line}")
            return []
        txs.append(tx)
        prev_row = tx
    return txs

def get_row_from_register_line(line, header):
    """
    Parse one register line into a Transaction object
    """
    if line.strip() == "":
        raise ValueError("The lines must be prepared by [clean_up_register_output](cci:1://file:///home/alen/src/interactive-brokers-flex-rs/src/ledger_reg_output_parser.rs:16:0-38:1)")

    has_symbol = line[1] != " "

    date_str = line[:10].strip()
    payee_str = line[11:46].strip()
    account_str = line[46:85].strip()
    amount_str = line[85:107].strip()

    # amount
    amount_parts = amount_str.split()
    if len(amount_parts) > 2:
        raise ValueError("Cannot parse Ledger amount string: {}".format(amount_str))    
    assert len(amount_parts) == 2
    amount = amount_parts[0].replace(",", "")

    tx = CommonTransaction()
    tx.date = datetime.strptime(date_str, ISO_DATE_FORMAT) if date_str else header.date
    tx.report_date = tx.date.strftime(ISO_DATE_FORMAT)
    tx.payee = payee_str if payee_str else header.payee
    tx.account = account_str
    tx.amount = Decimal(amount)
    tx.currency = "EUR"  # assuming EUR as the default currency
    tx.description = ""
    tx.symbol = payee_str.split()[0] if has_symbol else ""
    tx.type = ""

    return tx

def parse_distribution_report():
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

def parse_posting_row_test():
    """
    Test function to parse a posting row
    """
    date = datetime(2022, 12, 1)
    header = CommonTransaction(date=date, payee="Supermarket", account="Expenses:Food", amount=Decimal("15"), currency="EUR")
    line = """                                              Assets:Bank:Checking                              -15.00 EUR                    0"""
    actual = get_row_from_register_line(line, header)
    assert actual.date.year == 2022
    assert actual.report_date
    assert actual.payee == "Supermarket"
    assert actual.account == "Assets:Bank:Checking"
    assert actual.amount == Decimal("-15")
    assert actual.currency == "EUR"

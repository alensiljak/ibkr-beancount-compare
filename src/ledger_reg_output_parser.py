"""
Parser for Ledger's output of the [register] command.
"""

from datetime import datetime
from decimal import Decimal
from loguru import logger

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
        new_lines.append(line)
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

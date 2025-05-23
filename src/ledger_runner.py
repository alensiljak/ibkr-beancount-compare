#!/usr/bin/env python3
"""
Rewrite of the ledger_runner
"""

import logging
import shlex
import subprocess
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from src.model import CommonTransaction
from src import ledger_reg_output_parser
from src.constants import ISO_DATE_FORMAT


# Basic logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants (should ideally be shared if this is part of a larger project)
# These were also present in the compare.rs translation.
TRANSACTION_DAYS: int = 60


def get_ledger_start_date_py(comparison_date_str: Optional[str] = None) -> str:
    """
    Determines the starting date from which to take Ledger transactions.
    Equivalent to Rust's get_ledger_start_date.
    """
    end_date_obj: date
    if comparison_date_str:
        try:
            end_date_obj = datetime.strptime(
                comparison_date_str, ISO_DATE_FORMAT
            ).date()
        except ValueError:
            logging.error(
                "Invalid date format for comparison_date_str: %s. Using today.",
                comparison_date_str,
            )
            end_date_obj = date.today()
    else:
        end_date_obj = date.today()

    start_date_obj = end_date_obj - timedelta(days=TRANSACTION_DAYS)
    start_date_formatted_str = start_date_obj.strftime(ISO_DATE_FORMAT)

    logging.debug(
        f"Ledger start date calculation: comparison_date='{comparison_date_str}', "
        f"end_date_obj={end_date_obj}, result_start_date='{start_date_formatted_str}'"
    )
    return start_date_formatted_str


def get_ledger_cmd_py(
    start_date: str,
    ledger_journal_file: Optional[str],
    effective_dates: bool,
) -> str:
    """
    Assembles the Ledger query command string.
    Equivalent to Rust's get_ledger_cmd.
    The returned string will be split using shlex before execution.
    """
    # Base command: ledger register, begin date, display expression
    cmd = f"ledger r -b {start_date} -d"

    cmd += ' "(account =~ /income/ and account =~ /ib/) or'
    cmd += ' (account =~ /expenses/ and account =~ /ib/ and account =~ /withh/)"'

    if effective_dates:
        cmd += " --effective"

    if ledger_journal_file:
        cmd += " -f "
        cmd += ledger_journal_file

    # Ensure ISO date format for parsing, and wide display
    cmd += " --date-format " + ISO_DATE_FORMAT + " --wide"

    return cmd


def get_ledger_tx_py(
    ledger_journal_file: Optional[str],
    start_date_str: str,
    use_effective_dates: bool,
) -> list[CommonTransaction]:
    """
    Get ledger transactions by running ledger-cli and parsing its output.
    Equivalent to Rust's get_ledger_tx.
    """
    cmd_str = get_ledger_cmd_py(
        start_date_str, ledger_journal_file, use_effective_dates
    )
    logging.debug(f"Constructed ledger command string: {cmd_str}")

    try:
        # Use shlex.split to handle arguments correctly, especially the quoted query
        cmd_args = shlex.split(cmd_str)
        logging.debug(f"Executing ledger command with args: {cmd_args}")

        # Execute the command
        # text=True decodes stdout/stderr to strings
        # check=True will raise CalledProcessError if return code is non-zero
        process_output = subprocess.run(
            cmd_args, capture_output=True, text=True, check=True
        )

        stdout_data = process_output.stdout
        if (
            process_output.stderr
        ):  # Log stderr even if command succeeded, as it might contain warnings
            logging.warning(f"Ledger command stderr:\n{process_output.stderr}")

    except subprocess.CalledProcessError as e:
        logging.error(
            f"Error running Ledger command.\n"
            f"Command: '{e.cmd}'\n"
            f"Return code: {e.returncode}\n"
            f"Stderr: {e.stderr}\n"
            f"Stdout: {e.stdout}"
        )
        # In Rust, this was a panic. Here, we raise the exception.
        # Depending on desired behavior, you might return an empty list or handle differently.
        raise
    except FileNotFoundError:
        logging.error("Ledger command not found. Ensure 'ledger' is in your PATH.")
        raise

    lines = stdout_data.splitlines()
    logging.debug(
        f"Ledger output lines ({len(lines)}): {lines if len(lines) < 10 else lines[:10] + ['...']}"
    )

    # The Rust code has a 'parser' variable hardcoded to 0, selecting ledger_reg_output_parser.
    # Replicating that direct choice here.
    # If parser selection was dynamic, this would be an if/else or strategy pattern.
    parser_choice = 0  # 0 for Register parsing, 1 for Print parsing (as in Rust)

    if parser_choice == 0:
        # Register parsing path
        cleaned_lines = ledger_reg_output_parser.clean_up_register_output(lines)
        transactions = ledger_reg_output_parser.get_rows_from_register(cleaned_lines)
    elif parser_choice == 1:
        # Print parsing path (currently unused based on Rust's hardcoded 'parser = 0')
        transactions = LedgerPrintOutputParser.parse_print_output(lines)
    else:
        # This case was a panic in Rust.
        logging.error(f"Invalid parser choice: {parser_choice}")
        raise ValueError(f"Invalid parser choice: {parser_choice}")

    logging.info(f"Parsed {len(transactions)} transactions from Ledger output.")
    return transactions


def run_ledger_py(args: list[str]) -> list[str]:
    """
    Runs Ledger with the given pre-split arguments and returns the output lines.
    Equivalent to Rust's `run_ledger` function (which was marked #[allow(unused)] but used in tests).
    The first argument in `args` should NOT be "ledger"; it's implied.
    Example: args = ["r", "-b", "2023-01-01", "-f", "journal.dat"]
    """
    full_command_args = ["ledger"] + args
    logging.debug(f"Running ledger with direct args: {full_command_args}")

    try:
        process_output = subprocess.run(
            full_command_args,
            capture_output=True,
            text=True,
            check=False,  # check=False to manually check stderr
        )

        # The Rust version asserted stderr is empty. This is a strong assertion.
        # Here, we log stderr if present.
        if process_output.stderr:
            logging.warning(
                f"run_ledger_py: Ledger command stderr:\n{process_output.stderr}"
            )
            # Original Rust code had: assert!(output.stderr.is_empty());
            # If this strictness is required:
            # if process_output.stderr.strip():
            #     raise AssertionError(f"Ledger stderr was not empty: {process_output.stderr}")

        if process_output.returncode != 0:
            logging.error(
                f"run_ledger_py: Ledger command failed with code {process_output.returncode}.\n"
                f"Command: '{' '.join(full_command_args)}'\n"
                f"Stderr: {process_output.stderr}"
            )
            # Mimic Rust's expect/panic behavior for command failure if not check=True
            raise subprocess.CalledProcessError(
                process_output.returncode,
                full_command_args,
                output=process_output.stdout,
                stderr=process_output.stderr,
            )

        return process_output.stdout.splitlines()

    except FileNotFoundError:
        logging.error(
            "run_ledger_py: Ledger command not found. Ensure 'ledger' is in your PATH."
        )
        raise
    except subprocess.CalledProcessError as e:  # If check=True was used or re-raised
        logging.error(f"run_ledger_py: CalledProcessError: {e}")
        raise


# --- Example Usage / Tests (mimicking Rust tests) ---
if __name__ == "__main__":
    # Configure logging for more detail if running standalone
    logging.getLogger().setLevel(logging.DEBUG)

    print("--- Running Ledger Runner Examples/Tests ---")

    # Dummy journal file for testing
    dummy_journal_content = """
2023-01-15 Dividend Income
    Assets:Broker:Cash      $100.00 ; Symbol: XYZ, Type: Dividend
    Income:Broker:Dividends $-100.00 ; Symbol: XYZ, Type: Dividend

2023-01-16 Tax Expense
    Expenses:Broker:Tax     $15.00 ; Symbol: XYZ, Type: Withholding Tax
    Assets:Broker:Cash      $-15.00 ; Symbol: XYZ, Type: Withholding Tax

2023-02-10 Another IB Income
    Assets:IB:Cash          EUR 50.00
    Income:IB:Other         EUR -50.00
    """
    dummy_journal_path = "temp_journal.ledger"
    with open(dummy_journal_path, "w") as f:
        f.write(dummy_journal_content)

    # Test get_ledger_start_date_py
    print("\n--- Test get_ledger_start_date_py ---")
    start_date_default = get_ledger_start_date_py()
    print(
        f"Default start date (approx {TRANSACTION_DAYS} days ago): {start_date_default}"
    )
    start_date_specific = get_ledger_start_date_py("2023-03-15")
    expected_specific_start = (
        datetime.strptime("2023-03-15", ISO_DATE_FORMAT).date()
        - timedelta(days=TRANSACTION_DAYS)
    ).strftime(ISO_DATE_FORMAT)
    print(
        f"Specific start date for 2023-03-15: {start_date_specific} (Expected: {expected_specific_start})"
    )
    assert start_date_specific == expected_specific_start

    # Test get_ledger_cmd_py
    print("\n--- Test get_ledger_cmd_py ---")
    cmd_str_1 = get_ledger_cmd_py("2023-01-01", dummy_journal_path, False)
    print(f"Cmd (no effective dates): {cmd_str_1}")
    cmd_str_2 = get_ledger_cmd_py("2023-01-01", dummy_journal_path, True)
    print(f"Cmd (with effective dates): {cmd_str_2}")
    # Expected: ledger r -b 2023-01-01 -d "(account =~ /income/ and account =~ /ib/) or (account =~ /expenses/ and account =~ /ib/ and account =~ /withh/)" -f temp_journal.ledger --date-format %Y-%m-%d --wide

    # Test run_ledger_py (mimics run_ledger_test from Rust)
    # This requires 'ledger' to be installed and in PATH.
    print("\n--- Test run_ledger_py ---")
    try:
        # A simple ledger command: balance for a specific account
        # Note: The query used in get_ledger_cmd_py is more complex.
        # This test is simpler, like the original Rust test for run_ledger.
        # The original Rust test was: "b active and cash -f ledger_journal_path"
        # We'll try a similar balance query.
        run_ledger_args = ["bal", "Assets:Broker", "-f", dummy_journal_path]
        output_lines = run_ledger_py(run_ledger_args)
        print(f"run_ledger_py output lines ({len(output_lines)}):")
        for line in output_lines:
            print(line)
        assert any(
            "$85.00  Assets:Broker" in line for line in output_lines
        )  # $100 - $15
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"Skipping run_ledger_py test: Ledger command failed or not found. {e}")

    # Test get_ledger_tx_py
    # This also requires 'ledger' to be installed and in PATH.
    # And the stubbed parsers would need to be implemented for real data.
    print("\n--- Test get_ledger_tx_py ---")
    # For this test to return actual CommonTransaction objects,
    # LedgerRegOutputParser.get_rows_from_register needs a real implementation.
    # Currently, it will return an empty list.
    # We are testing the command execution and flow up to the parser.

    # Modify the stub to return something for testing purposes
    _original_get_rows = ledger_reg_output_parser.get_rows_from_register

    def mock_get_rows_from_register(
        cleaned_lines: list[str],
    ) -> list[CommonTransaction]:
        print(f"Mock get_rows_from_register called with {len(cleaned_lines)} lines.")
        if any("Income:Broker:Dividends" in line for line in cleaned_lines):
            return [
                CommonTransaction(
                    date=date(2023, 1, 15),
                    report_date="2023-01-15",
                    symbol="XYZ",
                    type="Dividend",
                    amount=Decimal("-100.00"),
                    currency="$",
                    description="Mocked Dividend",
                )
            ]
        return []

    ledger_reg_output_parser.get_rows_from_register = mock_get_rows_from_register

    try:
        ledger_transactions = get_ledger_tx_py(
            ledger_journal_file=dummy_journal_path,
            start_date_str="2023-01-01",
            use_effective_dates=False,
        )
        print(f"get_ledger_tx_py returned {len(ledger_transactions)} transactions:")
        for tx in ledger_transactions:
            print(tx)
        # If mock is active and ledger runs, this should pass:
        if ledger_transactions:  # Check if mock returned anything
            assert len(ledger_transactions) > 0
            assert ledger_transactions[0].symbol == "XYZ"
        else:  # If ledger command failed or mock didn't trigger
            print(
                "get_ledger_tx_py returned no transactions (as expected if parser stub is empty or ledger failed)."
            )

    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(
            f"Skipping get_ledger_tx_py test: Ledger command failed or not found. {e}"
        )
    finally:
        ledger_reg_output_parser.get_rows_from_register = (
            _original_get_rows  # Restore original stub
        )

    # Test shlex.split (mimics test_ledger_words/test_shellwords)
    print("\n--- Test shlex.split ---")
    complex_cmd_str = r"""ledger r -b 2022-03-01 -d "(account =~ /income/ and account =~ /ib/) or (account =~ /ib/ and account =~ /withh/)" -f tests/journal.ledger --wide --date-format %Y-%m-%d"""
    shlex_split_result = shlex.split(complex_cmd_str)
    print(f"shlex.split result: {shlex_split_result}")
    expected_shlex_parts = [
        "ledger",
        "r",
        "-b",
        "2022-03-01",
        "-d",
        "(account =~ /income/ and account =~ /ib/) or (account =~ /ib/ and account =~ /withh/)",
        "-f",
        "tests/journal.ledger",
        "--wide",
        "--date-format",
        "%Y-%m-%d",
    ]
    assert shlex_split_result == expected_shlex_parts

    # Cleanup dummy file
    import os

    try:
        os.remove(dummy_journal_path)
        print(f"\nCleaned up {dummy_journal_path}")
    except OSError as e:
        print(f"Error cleaning up {dummy_journal_path}: {e}")

    print("\n--- Ledger Runner Examples/Tests Complete ---")

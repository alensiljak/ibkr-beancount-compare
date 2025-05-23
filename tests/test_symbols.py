"""
Tests for the symbols module.
"""

import unittest
from main import compare
from src.model import CompareParams
from src.symbols import read_symbols, SymbolMetadata

# [test_log::test]
#     fn test_same_symbols_different_exchange() {
#         let cmp_params = CompareParams {
#             flex_report_path: Some("tests/same_symbol.xml".into()),
#             flex_reports_dir: None,
#             ledger_journal_file: Some("tests/same_symbol.ledger".into()),
#             symbols_path: "tests/symbols.csv".into(),
#             effective_dates: false,
#         };
#         let actual = compare(cmp_params).unwrap();

# //         let expected = r#"New: 2023-09-14/2023-09-15 ARCA:SDIV Dividend    5.04 USD, SDIV(US37960A6698) CASH DIVIDEND USD 0.21 PER SHARE (Ordinary Dividend)
# // New: 2023-09-21/2023-09-22 BVME.ETF:SDIV    Dividend   10.26 USD, SDIV(IE00077FRP95) CASH DIVIDEND USD 0.09 PER SHARE (Mixed Income)"#;
#         let expected = "";

#         assert_eq!(expected, actual);
#     }


class TestSymbols(unittest.TestCase):
    """
    Tests for the symbols module.
    """

    def test_same_symbols_different_exchange(self):
        cmp_params = CompareParams(
            flex_report_path="tests/same_symbol.xml",
            flex_reports_dir=None,
            ledger_journal_file="tests/same_symbol.ledger",
            symbols_path="tests/symbols.csv",
            effective_dates=False,
        )
        actual = compare(cmp_params)
        expected = ""
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()

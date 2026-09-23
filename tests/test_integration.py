import os
import pytest
from unittest.mock import patch
from src.main import main
import pandas as pd

@pytest.fixture(scope='function')
def input_folder():
    return 'data/sample'

@pytest.fixture(scope='function')
def output_file(tmp_path):
    return tmp_path / 'output_test.xlsx'

class TestIntegration:
    def test_main_complete(self, input_folder, output_file):  
        # Verify that the complete sample workflow runs successfully and produces the expected Excel report.
        main(input_folder, output_file)  

        assert os.path.exists(output_file), "Output file was not created"

        excel_file = pd.ExcelFile(output_file)
    
        expected_sheets = ['Summary', 'Cleaned Data', 'Exceptions', 'Processing Log']
        for sheet in expected_sheets:
            assert sheet in excel_file.sheet_names, f"Sheet '{sheet}' is missing from the output"

        # Verify the expected business processing counts: 121 source rows -> 118 valid rows, with 1 duplicate and 2 other invalid records.
        cleaned_df = pd.read_excel(output_file, sheet_name="Cleaned Data")
        exceptions_df = pd.read_excel(output_file, sheet_name="Exceptions")
        processing_log_df = pd.read_excel(output_file, sheet_name="Processing Log")

        # 118 valid records should remain.
        assert len(cleaned_df) == 118, "'Cleaned Data' sheet should contain 118 rows"

        # There should be 3 total exceptions: 1 duplicate + 2 other invalid records.
        assert len(exceptions_df) == 3, "'Exceptions' sheet should contain 3 rows"

        # Verify the source files account for all 121 input records.
        assert processing_log_df["Records Read"].sum() == 121, "Total records read should be 121"

        # Verify the processing log accounts for all valid records.
        assert processing_log_df["Valid"].sum() == 118, "Valid records should be 118"

        # Verify exactly one duplicate was found.
        assert processing_log_df["Duplicates"].sum() == 1, "There should be 1 duplicate record"

        # Verify two other exceptions were found.
        assert processing_log_df["Exceptions"].sum() == 2, "There should be 2 exceptions found"
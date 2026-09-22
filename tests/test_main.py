import pytest
from unittest.mock import patch
from src.main import (
    normalize_customer, normalize_product, normalize_category, normalize_date,
    validate_quantity, validate_unit_price, validate_missing_fields, find_missing_columns,
    calculate_sales_amount, extract_person_from_filename, read_excel_files
)
import pandas as pd

@pytest.fixture
def normalize_df():
    return pd.DataFrame({
        'Order ID': ['A0001', 'A0002'],
        'Quantity': [2, 5],
        'Unit Price': [1.50, 2.99],
        'Customer': [' John ', ' Jane '],
        'Product': [' Product 1 ', ' Product 2 '],
        'Category': [' category 1 ', ' category 2 '],
        'Date': ['01-01-2023', '2023-01-02'],
        'Sales Person': ['Bob', 'Charlie'],
        'Source File': ['Report_Bob.xlsx', 'Report_Charlie.xlsx']
    })

class TestNormalizationFunctions:
    def test_normalize_customer(self, normalize_df):
        result_df = normalize_customer(normalize_df)
        assert result_df['Customer'][0] == 'John'
        assert result_df['Customer'][1] == 'Jane'

    def test_normalize_product(self, normalize_df):
        result_df = normalize_product(normalize_df)
        assert result_df['Product'][0] == 'Product 1'
        assert result_df['Product'][1] == 'Product 2'

    def test_normalize_category(self, normalize_df):
        result_df = normalize_category(normalize_df)
        assert result_df['Category'][0] == 'Category 1'
        assert result_df['Category'][1] == 'Category 2'

    def test_normalize_date(self, normalize_df):
        result_df = normalize_date(normalize_df)
        assert result_df['Date'][0] == '2023-01-01'
        assert result_df['Date'][1] == '2023-01-02'

@pytest.fixture
def validate_df():
    return pd.DataFrame({
        'Order ID': [1, 2, 3],
        'Quantity': [5, -1, 2],
        'Unit Price': [2.99, 0, 3],
        'Customer': [' John ', ' Jane ', None],
        'Product': [' Product 1 ', ' Product 2 ', ''],
        'Category': [' category 1 ', ' category 2 ', ' category 3 '],
        'Date': ['2023-01-01', '2023-01-02', '2023-01-03'],
        'Sales Person': ['Bob', 'Charlie', 'Joe'],
        'Source File': ['Report_Bob.xlsx', 'Report_Charlie.xlsx', 'Report_Joe.xlsx']
    })

class TestValidationFunctions:
    def test_validate_quantity(self, validate_df):
        result_df, exceptions = validate_quantity(validate_df)
        assert len(result_df) == 2
        assert len(exceptions) == 1

    def test_validate_unit_price(self, validate_df):
        result_df, exceptions = validate_unit_price(validate_df)
        assert len(result_df) == 2
        assert len(exceptions) == 1

    def test_validate_missing_fields(self, validate_df):
        # Create a DataFrame with missing fields
        result_df, exceptions = validate_missing_fields(validate_df)
        assert len(result_df) == 2
        assert len(exceptions) == 1

class TestMissingColumns:
    def test_find_missing_columns(self):
        # Setup a DataFrame with missing columns
        df = pd.DataFrame({'Date': [], 'Order ID': []})
        missing_cols = find_missing_columns(df)
        assert 'Customer' in missing_cols
        assert 'Product' in missing_cols

class TestCalculateSalesAmount:
    def test_calculate_sales_amount(self, validate_df):
        result_df = calculate_sales_amount(validate_df)
        # Assuming Sales Amount is calculated as Quantity * Unit Price for simplicity
        expected_sales_amount = [5 * 2.99]
        assert result_df['Sales Amount'].values[0] == pytest.approx(expected_sales_amount[0])

class TestFilenameParsing:
    def test_extract_person_from_filename(self):
        filename = "Report_John.xlsx"
        person = extract_person_from_filename(filename)
        assert person == 'John'

class TestReadExcelFiles:
    @patch('os.listdir')
    def test_no_excel_files(self, mock_listdir):
        # Make os.listdir return a list of non-excel files
        mock_listdir.return_value = ['Sales_John.txt', 'Sales_Jane.doc']

        input_folder = 'path/to/your/input/folder'

        # This should raise FileNotFoundError because no Excel files are found
        with pytest.raises(FileNotFoundError):
            read_excel_files(input_folder)

    @patch('os.listdir')
    def test_no_files(self, mock_listdir):
        # Make os.listdir return an empty list when called
        mock_listdir.return_value = []

        input_folder = 'path/to/your/input/folder'

        # This should raise FileNotFoundError because no files are found
        with pytest.raises(FileNotFoundError):
            read_excel_files(input_folder)

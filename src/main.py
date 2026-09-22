import sys
import os

# Add the project root directory to sys.path
here = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(here, '..')
sys.path.insert(0, project_root)

import argparse
import logging
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from src.config import LOG_LEVEL, LOG_FILE

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)

def find_missing_columns(df):
    missing_columns = []

    if 'Date' not in df.columns:
        missing_columns.append('Date')
    if 'Order ID' not in df.columns:
        missing_columns.append('Order ID')
    if 'Customer' not in df.columns:
        missing_columns.append('Customer')
    if 'Product' not in df.columns:
        missing_columns.append('Product')
    if 'Category' not in df.columns:
        missing_columns.append('Category')
    if 'Quantity' not in df.columns:
        missing_columns.append('Quantity')
    if 'Unit Price' not in df.columns:
        missing_columns.append('Unit Price')

    return missing_columns

def normalize_customer(df):
    df['Customer'] = df['Customer'].str.strip()
    return df

def normalize_product(df):
    df['Product'] = df['Product'].str.strip()
    return df

def normalize_category(df):
    df['Category'] = df['Category'].str.strip().str.title()
    return df

def parse_date(date):
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y'):
        try:
            return pd.to_datetime(pd.Series([date]), format=fmt).dt.strftime('%Y-%m-%d')[0]
        except ValueError:
            continue
    return pd.NaT  # Return NaT if no valid date format is found

def normalize_date(df):
    df['Date'] = df['Date'].apply(parse_date)
    return df

def validate_quantity(df):
    exceptions = []
    exception_ids = []
    for index, row in df.iterrows():
        order_id = row['Order ID']
        file_name = row['Source File']

        #check for invalid Quantity values
        if pd.isnull(row['Quantity']) or row['Quantity'] <= 0:
            exception_ids.append(index)
            details = {
                'Source File': [file_name],
                'Row Number': [index + 2],
                'Order ID': [order_id],
                'Issue': ['Invalid Quantity'],
                'Action': ['Excluded']
            }
            exceptions.append(pd.DataFrame(details))
    df = df.drop(exception_ids).reset_index(drop=True)
    return df, exceptions

def validate_unit_price(df):
    exceptions = []
    exception_ids = []
    for index, row in df.iterrows():
        order_id = row['Order ID']
        file_name = row['Source File']

        if pd.isnull(row['Unit Price']) or row['Unit Price'] <= 0:
            exception_ids.append(index)
            details = {
                'Source File': [file_name],
                'Row Number': [index + 2],
                'Order ID': [order_id],
                'Issue': ['Invalid Unit Price'],
                'Action': ['Excluded']
            }
            exceptions.append(pd.DataFrame(details))
    df = df.drop(exception_ids).reset_index(drop=True)
    return df, exceptions

def validate_missing_fields(df):
    exceptions = []
    exception_ids = []
    for index, row in df.iterrows():
        order_id = row['Order ID']
        file_name = row['Source File']

        if pd.isnull(row).any():
            exception_ids.append(index)
            details = {
                'Source File': [file_name],
                'Row Number': [index + 2],
                'Order ID': [order_id],
                'Issue': ['Missing Field(s)'],
                'Action': ['Excluded']
            }
            exceptions.append(pd.DataFrame(details))
    df = df.drop(exception_ids).reset_index(drop=True)
    return df, exceptions

def remove_duplicates(df):
    exceptions = []
    first_occurrences = {}

    for index, row in df.iterrows():
        order_id = row['Order ID']
        file_name = row['Source File']

        if order_id in first_occurrences:
            details = {
                'Source File': [file_name],
                'Row Number': [index + 2],
                'Order ID': [order_id],
                'Issue': ['Duplicate Order ID'],
                'Action': ['Duplicate Removed']
            }
            exceptions.append(pd.DataFrame(details))
        else:
            # Track this as the first occurrence of the ID
            first_occurrences[order_id] = index

    df = df.loc[[first_occurrences[order_id] for order_id in first_occurrences]].reset_index(drop=True)
    return df, exceptions

def calculate_sales_amount(df):
    # Calculate Sales Amount
    df['Sales Amount'] = df['Quantity'] * df['Unit Price']
    return df

def create_summary(df):
    # Calculate overall metrics
    total_sales = df['Sales Amount'].sum()
    orders = len(df)
    units_sold = df['Quantity'].sum()
    avg_order_value = total_sales / orders if orders > 0 else 0

    # Prepare summary data
    company_name = "Island Outdoor Supply"
    reporting_period = f"{pd.to_datetime(df['Date'].min(), errors='coerce').strftime('%b %d, %Y')} - {pd.to_datetime(df['Date'].max()).strftime('%b %d, %Y')}"
    generated_timestamp = datetime.now().strftime("%b %d, %Y %H:%M:%S")

    overall_metrics = pd.DataFrame({
        'Metrics': ['Total Sales', 'Orders', 'Units Sold', 'Average Order Value'],
        'Value': [f"${total_sales:,.2f}", orders, units_sold, f"${avg_order_value:,.2f}"]
    })

    sales_by_representative = df.groupby('Sales Person').agg({
        'Order ID': 'count',
        'Quantity': 'sum',
        'Sales Amount': 'sum'
    }).rename(columns={'Sales Person': 'Representative', 'Order ID': 'Orders', 'Quantity': 'Units', 'Sales Amount': 'Sales'}).reset_index()
    sales_by_representative['Sales'] = pd.to_numeric(sales_by_representative['Sales'], errors='coerce')
    sales_by_representative['Sales'] = sales_by_representative['Sales'].apply(lambda x: f"${x:,.2f}")

    sales_by_category = df.groupby('Category').agg({
        'Order ID': 'count',
        'Quantity': 'sum',
        'Sales Amount': 'sum'
    }).rename(columns={'Category': 'Category', 'Order ID': 'Orders', 'Quantity': 'Units', 'Sales Amount': 'Sales'}).reset_index()
    sales_by_category['Sales'] = pd.to_numeric(sales_by_category['Sales'], errors='coerce')
    sales_by_category['Sales'] = sales_by_category['Sales'].apply(lambda x: f"${x:,.2f}")

    # Create summary DataFrame
    summary_df = pd.DataFrame([
        [f"{company_name}"],
        ["Weekly Sales Report"],
        ["Reporting Period: " + reporting_period],
        ["Generated: " + generated_timestamp],
        [""],
        ["Overall Metrics"]
    ])

    return summary_df, overall_metrics, sales_by_representative, sales_by_category

def create_proccessing_log(df, cleaned_df, exceptions_df):
    processing_logs = []
    df_by_source = df.groupby('Source File').agg({
        'Order ID': 'count'
    }).rename(columns={'Source File': 'Source File', 'Order ID': 'Orders'}).reset_index()

    for index, row in df_by_source.iterrows():
        source_file = row['Source File']

        exceptions_count = 0
        duplicate_count = 0
        if not exceptions_df.empty:
            exceptions_count = len(exceptions_df[(exceptions_df['Source File'] == source_file) & (exceptions_df['Action'] == 'Excluded')])
            duplicate_count = len(exceptions_df[(exceptions_df['Source File'] == source_file) & (exceptions_df['Issue'] == 'Duplicate Order ID')])

        valid_count = 0
        if not cleaned_df.empty:
            valid_count = len(cleaned_df[cleaned_df['Source File'] == source_file])

        processing_log = {
            'Source File': [source_file],
            'Records Read': [row['Orders']],
            'Valid': [valid_count],
            'Exceptions': [exceptions_count],
            'Duplicates': [duplicate_count]
        }
        processing_logs.append(pd.DataFrame(processing_log))

    processing_log_df = pd.concat(processing_logs, axis=0, ignore_index=True)
    return processing_log_df

def extract_person_from_filename(filename):
    # Regex pattern to match *_PersonName.*
    pattern = r'.*_(.+)\.[a-zA-Z0-9]+$'

    # Match the filename against the pattern
    match = re.match(pattern, filename)
    if match:
        # Extract and return the "PersonName" part
        person = match.group(1)
        return person
    else:
        # If no match, use the entire filename without extension as fallback
        name_without_ext = os.path.splitext(filename)[0]
        return name_without_ext

def read_excel_files(input_folder):
    all_df = []

    excel_files = [f for f in os.listdir(input_folder) if f.endswith(".xlsx")]
    if not excel_files:
        raise FileNotFoundError(f"No Excel files (.xlsx) found in the directory: {input_folder}")
    
    for file in excel_files:
        file_path = os.path.join(input_folder, file)

        logging.info(f"Reading file: {file}")
        df = pd.read_excel(file_path)

        missing_columns = find_missing_columns(df)
        if missing_columns:
            comma_separated_str = ', '.join(missing_columns)
            raise KeyError(f"{file} is missing the column(s) {comma_separated_str}")
        
        df['Sales Person'] = extract_person_from_filename(file)
        df['Source File'] = file

        all_df.append(df)

    return pd.concat(all_df, axis=0, ignore_index=True)

def process_df(df):
    all_exceptions = []

    logging.info("Normalizing Dates")
    normalized_df = normalize_date(df)

    logging.info("Normalizing Customer Names")
    normalized_df = normalize_customer(normalized_df)

    logging.info("Normalizing Product Names")
    normalized_df = normalize_product(normalized_df)

    logging.info("Normalizing Category Names")
    normalized_df = normalize_category(normalized_df)

    logging.info("Validating Quantity Values")
    validated_df, quantity_exceptions_details = validate_quantity(normalized_df)
    all_exceptions.extend(quantity_exceptions_details)

    logging.info("Validating Unit Price Values")
    validated_df, unit_price_exceptions_details = validate_unit_price(validated_df)
    all_exceptions.extend(unit_price_exceptions_details)

    logging.info("Validating Required Fields")
    validated_df, missing_fields_exceptions_details = validate_missing_fields(validated_df)
    all_exceptions.extend(missing_fields_exceptions_details)

    logging.info("Identifying Duplicates")
    deduped_df, duplicate_exceptions_details = remove_duplicates(validated_df)
    all_exceptions.extend(duplicate_exceptions_details)

    # Calculate Sales Amount on the normalized, validated, and deduped data
    logging.info("Calculating Sales Amounts")
    final_df = calculate_sales_amount(deduped_df)

    all_exceptions_df = pd.concat(all_exceptions, axis=0, ignore_index=True)

    return final_df, all_exceptions_df

def main(input_folder, output_file):
    logging.info("Script start")

    try:
        df = read_excel_files(input_folder)
        final_df, exceptions_df = process_df(df)
        final_df = final_df[['Date', 'Order ID', 'Product', 'Category', 'Quantity', 'Unit Price', 'Sales Person', 'Sales Amount', 'Source File']]

        logging.info("Generating Summary")
        summary_df, overall_metrics, sales_by_rep, sales_by_cat = create_summary(final_df)

        logging.info("Generating Process Logs")
        processing_log_df = create_proccessing_log(df, final_df, exceptions_df)

        overall_metrics_startrow = len(summary_df)
        sales_by_rep_startrow = overall_metrics_startrow + len(overall_metrics) + 2
        sales_by_cat_startrow = sales_by_rep_startrow + len(sales_by_rep) + 2
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Summary', startrow=0, index=False, header=False)
            overall_metrics.to_excel(writer, sheet_name='Summary', startrow=overall_metrics_startrow, index=False)
            sales_by_rep.to_excel(writer, sheet_name='Summary', startrow=sales_by_rep_startrow, index=False)
            sales_by_cat.to_excel(writer, sheet_name='Summary', startrow=sales_by_cat_startrow, index=False)
            final_df.to_excel(writer, sheet_name='Cleaned Data', index=False)
            exceptions_df.to_excel(writer, sheet_name='Exceptions', index=False)
            processing_log_df.to_excel(writer, sheet_name='Processing Log', index=False)

        logging.info(f"Report written to: {output_file}")
        logging.info("Script successful.")
    except FileNotFoundError as fnfe:
        logging.error(fnfe)
    except KeyError as ke:
        logging.error(ke)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read Excel files from a folder and combine, clean, validate, calculate, and summarize the data into a management report.")
    parser.add_argument("-i", "--input-folder", type=str, required=True, help="Folder containing the Excel files to process.")
    parser.add_argument("-o", "--output-file", type=str, required=True, help="File path for management report.")
    args = parser.parse_args()
    main(args.input_folder, args.output_file)

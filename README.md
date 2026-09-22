# Automated Weekly Sales Report

This script processes Excel files from a specified input folder, combines the data, cleans it, validates records, calculates sales amounts, and generates a management report.

## Features
- Combines, cleans, validates, calculates, and summarizes sales data from multiple Excel files.
- Generates a management report with summary statistics and metrics.

## Installation
Install the required dependencies using pip and the requirements.txt file:
```bash
pip install -r requirements.txt
```

## Usage
Run the script using command-line arguments:
```bash
python src/main.py -i /path/to/input/folder -o /path/to/output/file.xlsx
```

### Arguments
- `-i`, `--input-folder`: Folder containing the Excel files to process.
- `-o`, `--output-file`: File path for management report.

## Files and Directories
- `src/main.py`: Main script for processing sales data.
- `config.py`: Configuration file for logging settings (LOG_FILE, LOG_LEVEL).

## Configuration
Configure the `config.py` file to set up logging:
```python
# config.py
LOG_FILE = 'path/to/log/file.log'
LOG_LEVEL = 'INFO'  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

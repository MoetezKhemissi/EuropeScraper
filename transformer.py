import os
import re
import logging
import pandas as pd
from pdfminer.high_level import extract_text
from tqdm import tqdm

# ====================== Configuration ======================

# Directory containing the PDFs
PDF_DIR = 'pdfs'  # Change if your folder has a different name or path

# Output CSV file
OUTPUT_CSV = 'extracted_texts.csv'

# Log file
LOG_FILE = 'pdf_extraction.log'

# ============================================================

def setup_logging():
    """
    Sets up logging configuration.
    """
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s:%(message)s',
        filemode='w'  # Overwrite the log file each time
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def extract_text_from_pdf(pdf_path, password=None):
    """
    Extracts text from a PDF file.

    Args:
        pdf_path (str): The full path to the PDF file.
        password (str, optional): Password for encrypted PDFs.

    Returns:
        str: Extracted text content.
    """
    try:
        text = extract_text(pdf_path, password=password)
        return text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return ""

def extract_date_from_filename(filename):
    """
    Extracts the date from the PDF filename.

    Assumes the filename contains a date in the format (YYYY)MM-DD.

    Args:
        filename (str): The PDF filename.

    Returns:
        str: Extracted date in YYYY-MM-DD format or empty string if not found.
    """
    match = re.search(r'\((\d{4})\)(\d{2})-(\d{2})', filename)
    if match:
        year, month, day = match.groups()
        return f"{year}-{month}-{day}"
    return ""

def main():
    # Setup logging
    setup_logging()
    logging.info("Starting PDF text extraction process.")

    # Check if PDF directory exists
    if not os.path.isdir(PDF_DIR):
        logging.error(f"PDF directory '{PDF_DIR}' does not exist.")
        return

    # List all PDF files in the directory
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
    if not pdf_files:
        logging.error(f"No PDF files found in '{PDF_DIR}'.")
        return

    logging.info(f"Found {len(pdf_files)} PDF files in '{PDF_DIR}'.")

    # Initialize a list to hold data
    data = []

    # Iterate over each PDF file with a progress bar
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        logging.info(f"Processing file: {pdf_file}")

        text = extract_text_from_pdf(pdf_path)

        if text:
            date = extract_date_from_filename(pdf_file)
            data.append({
                'filename': pdf_file,
                'date': date,
                'text': text.strip()
            })
            logging.info(f"Extracted text from {pdf_file}.")
        else:
            logging.warning(f"No text extracted from {pdf_file}.")

    if not data:
        logging.error("No text was extracted from any PDF files.")
        return

    # Create a DataFrame from the data
    df = pd.DataFrame(data)

    # Save the DataFrame to a CSV file
    try:
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
        logging.info(f"All texts have been extracted and saved to '{OUTPUT_CSV}'.")
    except Exception as e:
        logging.error(f"Failed to save data to CSV: {e}")

    logging.info("PDF text extraction process completed.")

if __name__ == "__main__":
    main()

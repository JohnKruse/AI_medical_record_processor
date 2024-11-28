import os
import logging
import shutil
from text_extraction import extract_text_from_txt, extract_text_from_pdf, extract_text_from_image, extract_text_from_docx, extract_text_from_excel

def process_file(file_path, config, openai_api_key):  # Added openai_api_key parameter
    ext = os.path.splitext(file_path)[1].lower()
    logging.debug(f"Processing file: {file_path} with extension: {ext}")
    
    if ext == '.txt':
        text = extract_text_from_txt(file_path)
    elif ext == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif ext in ['.png', '.jpg', '.jpeg', '.tiff']:
        lang = config.get('ocr_language', 'eng+ita')  # Extract language from config
        text = extract_text_from_image(file_path, lang)  # Pass the language code
    elif ext == '.docx':
        text = extract_text_from_docx(file_path)
    elif ext in ['.xls', '.xlsx']:
        text = extract_text_from_excel(file_path)
    else:
        logging.warning(f"Unrecognized file type for file: {file_path}. Skipping processing.")
        return ''  # Return empty string for unrecognized file types
    
    logging.debug(f"Extracted text: {text[:100]}...")  # Log the first 100 characters of the extracted text
    
    if not text:
        logging.warning(f"No valid text extracted from {file_path}")
    
    return text

def is_continuation_of_previous(current_file_path, previous_file_path):
    """Determine if the current file is a continuation of the previous file."""
    if previous_file_path is None:
        return False
    
    # Example logic: Check if the filenames share a common prefix
    current_base = os.path.basename(current_file_path)
    previous_base = os.path.basename(previous_file_path)
    
    return current_base.startswith(previous_base.split('_')[0])

def clear_output_location(config):
    """Clear the output location specified in the configuration."""
    output_location = config['output_location']
    if os.path.exists(output_location):
        logging.info(f"Clearing output location: {output_location}")
        shutil.rmtree(output_location)
        os.makedirs(output_location, exist_ok=True)
    else:
        logging.info(f"Output location does not exist, creating: {output_location}")
        os.makedirs(output_location, exist_ok=True)

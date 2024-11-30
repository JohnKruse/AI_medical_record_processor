import os
import sys
import yaml
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime as dt  # Renaming the import to avoid conflicts
from typing import Dict, Any  # Importing Dict and Any for type hinting
import json  # Add this at the top with other imports
import pandas as pd
from translator import Translator
import shutil

# Import custom utilities
from ai_utils import *

# Import local modules
from checksum_utils import *
from file_processing import *
from metadata import find_first_date_in_text, create_new_filename
from document_utils import *

def setup_logging():
    """Configure logging with custom file size management."""
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Change to DEBUG level
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Set up the rotating file handler
    log_filename = os.path.join(os.path.dirname(__file__), 'medical_rec_process.log')
    handler = RotatingFileHandler(
        log_filename,
        maxBytes=250000,  # 250kB
        backupCount=2     # Keep 2 backup files
    )
    
    # Create formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)  # Set handler to DEBUG level too
    
    # Add the handler to the logger
    logger.addHandler(handler)
    
    # Initial log messages
    logging.info("=" * 80)
    logging.info("NEW RUN STARTING " + "=" * 63)
    logging.info("=" * 80)
    logging.info("Starting medical records processing")

def substitute_config_variables(config_dict, translator=None):
    """
    Recursively process all strings in config dictionary and substitute variables.
    Currently handles ${output_language} substitution.
    """
    if not isinstance(config_dict, dict):
        return config_dict
        
    # Initialize translator if not provided
    if translator is None:
        translator = Translator(os.path.join(os.path.dirname(__file__), 'translations'))
    
    # Get language name for substitution
    output_language = config_dict.get('output_language', 'en')
    language_name = translator.get_language_name(output_language)
    
    def _substitute_in_value(value):
        if isinstance(value, str):
            return value.replace('${output_language}', language_name)
        elif isinstance(value, dict):
            return {k: _substitute_in_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_substitute_in_value(item) for item in value]
        return value
    
    return {k: _substitute_in_value(v) for k, v in config_dict.items()}

def load_config(config_path):
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Convert boolean strings to actual booleans
    if 'skip_processed_files' in config:
        if isinstance(config['skip_processed_files'], str):
            config['skip_processed_files'] = config['skip_processed_files'].lower() == 'true'
    
    # Substitute variables in config
    config = substitute_config_variables(config)
    
    logging.info(f"Loaded configuration from {config_path}")
    logging.info(f"Skip processed files: {config['skip_processed_files']} (type: {type(config['skip_processed_files'])})")
    
    # Log the substituted role prompt
    if 'ai_processing' in config and 'role_prompt' in config['ai_processing']:
        logging.info(f"Role prompt after substitution: {config['ai_processing']['role_prompt']}")
    
    return config

def ensure_directories(config):
    """Ensure required directories exist."""
    scans_location = config['scans_location']
    output_location = config['output_location']
    
    # Check and create scans directory
    if not os.path.exists(scans_location):
        logging.info(f"Creating scans directory: {scans_location}")
        os.makedirs(scans_location, exist_ok=True)
    
    # Check and create output directory
    if not os.path.exists(output_location):
        logging.info(f"Creating output directory: {output_location}")
        os.makedirs(output_location, exist_ok=True)
    
    return scans_location, output_location

def process_files(config):
    """Main file processing logic."""
    scans_location, output_location = ensure_directories(config)
    
    # Ensure output location
    ensure_output_location(config)
    
    output_html = config.get('output_html', 'output.html')
    skip_processed = config['skip_processed_files']
    skip_process_review_interval = config.get('skip_process_review_interval', 180)
    checksums_file = os.path.join(output_location, 'data_files', 'processed_files.json')
    extracted_data_file = os.path.join(output_location, 'data_files', 'extracted_data.csv')
    
    logging.info(f"Processing settings: skip_processed={skip_processed}, review_interval={skip_process_review_interval} days")
    
    # Load existing checksums and processed data
    processed_checksums = load_processed_checksums(checksums_file)
    existing_records = []
    
    if skip_processed and os.path.exists(extracted_data_file):
        try:
            existing_df = pd.read_csv(extracted_data_file)
            existing_records = existing_df.to_dict('records')
            logging.info(f"Loaded {len(existing_records)} existing records from {extracted_data_file}")
        except Exception as e:
            logging.error(f"Error loading existing records: {e}")
    
    new_records = []
    previous_file = None
    current_datetime = dt.now()
    
    # Get the OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY') or config.get('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OpenAI API Key is not set")
    
    # Process files
    files_found = False
    all_files = []
    for root, dirs, files in os.walk(scans_location):
        if files:
            files_found = True
            for file in sorted(files):
                if not file.startswith('.'):
                    all_files.append((root, file))
    
    if files_found:
        total_files = len(all_files)
        print(f"\nFound {total_files} files to examine")
        
        for idx, (root, file) in enumerate(all_files, 1):
            file_path = os.path.join(root, file)
            file_checksum = calculate_checksum(file_path)
            
            # Check if file should be skipped
            should_process = True
            if skip_processed and file_checksum in processed_checksums:
                last_processed_str = processed_checksums[file_checksum].get('processed_date')
                if last_processed_str:
                    last_processed = dt.strptime(last_processed_str, '%Y-%m-%d %H:%M:%S')
                    days_since_processed = (current_datetime - last_processed).days
                    
                    if days_since_processed < skip_process_review_interval:
                        print(f"Skipping file processed {days_since_processed} days ago: {file}")
                        should_process = False
            
            if should_process:
                try:
                    print(f"\nProcessing file {idx} / {total_files}: {file}")
                    
                    # Process the file
                    text = process_file(file_path, config, openai_api_key)
                    if not text:
                        continue
                    
                    # Create record
                    record = {
                        'file_path': file_path,
                        'original_filename': file,
                        'text': text,
                        'checksum': file_checksum,
                        'processed_date': current_datetime.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    new_records.append(record)
                    processed_checksums[file_checksum] = {
                        'processed_date': current_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                        'original_file': file
                    }
                    
                    save_processed_checksums(checksums_file, processed_checksums)
                    
                except Exception as e:
                    logging.error(f"Error processing {file}: {str(e)}")
                    continue
    
    # Combine existing and new records
    all_records = existing_records + new_records
    
    if not all_records:
        logging.warning("No records to process")
        return [], processed_checksums, checksums_file, openai_api_key
    
    # Only process new records through AI
    if new_records:
        new_records_df = pd.DataFrame(new_records)
        processed_new_df = batch_process_medical_records(new_records_df, config, openai_api_key)
        
        # Convert existing records to DataFrame
        if existing_records:
            existing_df = pd.DataFrame(existing_records)
            # Combine existing and new records
            records_df = pd.concat([existing_df, processed_new_df], ignore_index=True)
        else:
            records_df = processed_new_df
    else:
        # If no new records, just use existing ones
        records_df = pd.DataFrame(existing_records)
    
    return records_df.to_dict('records'), processed_checksums, checksums_file, openai_api_key

def batch_process_medical_records(records_df: pd.DataFrame, config: Dict[str, Any], openai_api_key: str) -> pd.DataFrame:
    logging.info("Starting batch_process_medical_records")
    logging.info(f"Batch processing medical records with DataFrame of size: {len(records_df)}")
    
    print(f"\nProcessing {len(records_df)} records through AI analysis...")
    
    # Get current datetime once
    current_datetime = dt.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create summary and new columns if they don't exist
    new_columns = {
        'summary': '',
        'visit_type': '',
        'provider_name': '',
        'provider_facility': '',
        'primary_condition': '',
        'diagnoses': [],
        'treatments': [],
        'medications': [],
        'test_results': [],
        'treatment_date': None,
        'ai_treatment_date': None,  # New column for AI-extracted date
        'last_processed': current_datetime,  # New column for processing timestamp
        'patient_first_name': '',  # Add patient columns
        'patient_middle_name': '',
        'patient_last_name': ''
    }
    
    # Initialize new columns with default values if they don't exist
    for col, default_value in new_columns.items():
        if col not in records_df.columns:
            if isinstance(default_value, list):
                records_df[col] = [[] for _ in range(len(records_df))]
            else:
                records_df[col] = pd.Series([default_value] * len(records_df))
    
    # Extract treatment dates from text using first date found
    records_df['treatment_date'] = records_df['text'].apply(find_first_date_in_text)
    logging.info("Extracted treatment dates from text")

    logging.info("Setting AI API parameters")
    role_prompt = config['ai_processing']['role_prompt']
    model_name = config['ai_processing']['model_name']
    max_tokens = config['ai_processing']['max_tokens']
    temperature = config['ai_processing']['temperature']
    function_schema = config['ai_processing'].get('function_schema', None)
    
    # Log the function schema
    logging.info(f"Function schema: {json.dumps(function_schema, indent=2)}")
    
    # Create a single question that asks for structured analysis
    analysis_question = "Analyze this medical record and provide structured information including a summary of the visit/examination."
    
    for index, record in records_df.iterrows():
        print(f"\nAnalyzing record {index + 1} / {len(records_df)}: {record['original_filename']}")
        logging.debug(f"Processing record at index {index}: {record['file_path']}")
        
        text = record['text']
        file_path = record['file_path']
        
        if text:
            try:
                print("Extracting medical information...")
                # Process with AI API using the imported function
                logging.debug(f"Calling AI API with text: {text[:50]}...")
                ai_response = query_openai_gptX_with_schema(
                    text=text,
                    questions=[analysis_question],  # Single question for structured analysis
                    role_prompt=role_prompt,
                    model_name=model_name,
                    api_key=openai_api_key,
                    file_path=None,
                    function_schema=function_schema,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                logging.debug(f"AI API response: {ai_response}")
                print("Analysis complete")

                # Parse response and store in separate columns
                response_text = ai_response.get(analysis_question, '{}')
                try:
                    parsed_response = json.loads(response_text)
                    logging.debug(f"Parsed response: {parsed_response}")
                    
                    # Store each field in its own column
                    records_df.at[index, 'primary_condition'] = parsed_response.get('primary_condition', '')
                    records_df.at[index, 'diagnoses'] = parsed_response.get('diagnoses', [])
                    records_df.at[index, 'treatments'] = parsed_response.get('treatments', [])
                    
                    # Store the summary and visit type
                    summary = parsed_response.get('summary', '')
                    records_df.at[index, 'summary'] = summary
                    records_df.at[index, 'visit_type'] = parsed_response.get('visit_type', '')
                    
                    # Store provider information
                    provider = parsed_response.get('provider', {})
                    records_df.at[index, 'provider_name'] = provider.get('name', '')
                    records_df.at[index, 'provider_facility'] = provider.get('facility', '')
                    
                    # Store patient information
                    patient = parsed_response.get('patient', {})
                    records_df.at[index, 'patient_first_name'] = patient.get('first_name', '')
                    records_df.at[index, 'patient_middle_name'] = patient.get('middle_name', '')
                    records_df.at[index, 'patient_last_name'] = patient.get('last_name', '')
                    
                    # Store AI-extracted treatment date
                    ai_date = parsed_response.get('treatment_date', '')
                    records_df.at[index, 'ai_treatment_date'] = ai_date
                    
                    # If regex didn't find a date but AI did, use the AI date
                    if pd.isna(records_df.at[index, 'treatment_date']) and ai_date:
                        records_df.at[index, 'treatment_date'] = ai_date
                        logging.info(f"Using AI-extracted date: {ai_date}")
                    
                    # Extract medication names into a list
                    medications = parsed_response.get('medications', [])
                    med_list = []
                    for med in medications:
                        if isinstance(med, dict) and 'name' in med:
                            med_info = f"{med['name']}"
                            if 'dosage' in med:
                                med_info += f" ({med['dosage']})"
                            med_list.append(med_info)
                    records_df.at[index, 'medications'] = med_list
                    
                    # Format test results into a list
                    test_results = parsed_response.get('test_results', [])
                    if isinstance(test_results, dict):
                        test_results = [test_results]  # Convert single result to list
                    test_list = []
                    for test in test_results:
                        if isinstance(test, dict):
                            test_info = f"{test.get('name', '')}: {test.get('value', '')}"
                            if 'interpretation' in test:
                                test_info += f" - {test['interpretation']}"
                            test_list.append(test_info)
                    records_df.at[index, 'test_results'] = test_list
                    
                    logging.debug(f"Structured data stored for index {index}")
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse JSON response: {str(e)}")
                    # Set empty values for all columns on error
                    for col, default_value in new_columns.items():
                        records_df.at[index, col] = default_value
            except Exception as e:
                logging.error(f"Error processing text: {str(e)}")
                raise
        else:
            logging.warning(f"No text found for record at index {index}, sending file to API")
            try:
                # Process with AI API using the raw file
                ai_response = query_openai_gptX_with_schema(
                    text=None,  # No text provided
                    questions=[analysis_question],  # Single question for structured analysis
                    role_prompt=role_prompt,
                    model_name=model_name,
                    api_key=openai_api_key,
                    file_path=file_path,
                    function_schema=function_schema,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                response_text = ai_response.get(analysis_question, '{}')
                try:
                    parsed_response = json.loads(response_text)
                    logging.debug(f"Parsed response: {parsed_response}")
                    
                    # Store each field in its own column
                    records_df.at[index, 'primary_condition'] = parsed_response.get('primary_condition', '')
                    records_df.at[index, 'diagnoses'] = parsed_response.get('diagnoses', [])
                    records_df.at[index, 'treatments'] = parsed_response.get('treatments', [])
                    
                    # Store the summary and visit type
                    summary = parsed_response.get('summary', '')
                    records_df.at[index, 'summary'] = summary
                    records_df.at[index, 'visit_type'] = parsed_response.get('visit_type', '')
                    
                    # Store provider information
                    provider = parsed_response.get('provider', {})
                    records_df.at[index, 'provider_name'] = provider.get('name', '')
                    records_df.at[index, 'provider_facility'] = provider.get('facility', '')
                    
                    # Store patient information
                    patient = parsed_response.get('patient', {})
                    records_df.at[index, 'patient_first_name'] = patient.get('first_name', '')
                    records_df.at[index, 'patient_middle_name'] = patient.get('middle_name', '')
                    records_df.at[index, 'patient_last_name'] = patient.get('last_name', '')
                    
                    # Store AI-extracted treatment date
                    ai_date = parsed_response.get('treatment_date', '')
                    records_df.at[index, 'ai_treatment_date'] = ai_date
                    
                    # If regex didn't find a date but AI did, use the AI date
                    if pd.isna(records_df.at[index, 'treatment_date']) and ai_date:
                        records_df.at[index, 'treatment_date'] = ai_date
                        logging.info(f"Using AI-extracted date: {ai_date}")
                    
                    # Extract medication names into a list
                    medications = parsed_response.get('medications', [])
                    med_list = []
                    for med in medications:
                        if isinstance(med, dict) and 'name' in med:
                            med_info = f"{med['name']}"
                            if 'dosage' in med:
                                med_info += f" ({med['dosage']})"
                            med_list.append(med_info)
                    records_df.at[index, 'medications'] = med_list
                    
                    # Format test results into a list
                    test_results = parsed_response.get('test_results', [])
                    if isinstance(test_results, dict):
                        test_results = [test_results]  # Convert single result to list
                    test_list = []
                    for test in test_results:
                        if isinstance(test, dict):
                            test_info = f"{test.get('name', '')}: {test.get('value', '')}"
                            if 'interpretation' in test:
                                test_info += f" - {test['interpretation']}"
                            test_list.append(test_info)
                    records_df.at[index, 'test_results'] = test_list
                    
                    logging.debug(f"Structured data stored for index {index}")
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse JSON response: {str(e)}")
                    # Set empty values for all columns on error
                    for col, default_value in new_columns.items():
                        records_df.at[index, col] = default_value
            except Exception as e:
                logging.error(f"Error processing file: {str(e)}")
                # Set empty values for all columns on error
                for col, default_value in new_columns.items():
                    records_df.at[index, col] = default_value
    
    print("\nAI analysis complete for all records")
    return records_df

def ensure_output_location(config):
    """Set up the output location with proper subdirectories."""
    output_location = config['output_location']
    
    # Create main output directory and subdirectories if they don't exist
    os.makedirs(output_location, exist_ok=True)
    os.makedirs(os.path.join(output_location, 'html'), exist_ok=True)
    os.makedirs(os.path.join(output_location, 'records'), exist_ok=True)
    os.makedirs(os.path.join(output_location, 'data_files'), exist_ok=True)
    
    # Copy logo and other assets only if they don't exist
    web_page_dir = os.path.join(os.path.dirname(__file__), 'web_page')
    output_html_dir = os.path.join(output_location, 'html')
    
    # Copy Logo.png if it doesn't exist
    logo_target = os.path.join(output_html_dir, 'Logo.png')
    if not os.path.exists(logo_target):
        shutil.copy2(
            os.path.join(web_page_dir, 'Logo.png'),
            logo_target
        )
    
    # Create README.md if it doesn't exist
    readme_path = os.path.join(output_location, 'README.md')
    if not os.path.exists(readme_path):
        readme_content = """# Medical Records Processing Output

This directory contains processed medical records and associated data files.

## Directory Structure

- `medical_records_Dente.html` - Main viewer interface for browsing records
- `records/` - Processed and renamed medical record files
- `data_files/` - Data files including CSV exports and processing metadata
- `html/` - Web interface assets (CSS, JavaScript, images)

## Files

### Data Files
- `data_files/extracted_data.csv` - Structured data extracted from medical records
- `data_files/processed_files.json` - Processing metadata and file tracking

### Web Interface
The main HTML viewer provides:
- Chronological listing of medical records
- Interactive record viewing
- Record details and summaries
- Print functionality
- Keyboard navigation (up/down arrows)

Generated on: """ + dt.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    logging.info(f"Ensured output directories exist at: {output_location}")

def main():
    """Main entry point of the program."""
    setup_logging()
    
    try:
        logging.info("Loading configuration")
        config = load_config('config/config.yaml')
        
        # Ensure output location
        ensure_output_location(config)
        
        # Process files and get records
        records = []
        processed_checksums = {}
        checksums_file = ""
        openai_api_key = ""
        
        try:
            records, processed_checksums, checksums_file, openai_api_key = process_files(config)
        except Exception as e:
            logging.error(f"Error processing files: {str(e)}")
            raise
        
        if not records:
            logging.warning("No records to process")
            return
        
        # Convert to DataFrame
        logging.info("Processing records through AI")
        records_df = pd.DataFrame(records)
        
        # Create filenames and copy files
        output_location = config['output_location']
        records_dir = os.path.join(output_location, 'records')
        
        for index, record in records_df.iterrows():
            try:
                # Create new filename using AI-processed data
                new_filename = create_new_filename({}, record.to_dict(), config)
                ext = os.path.splitext(record['original_filename'])[1]
                new_filename = f"{new_filename}{ext}"
                new_file_path = os.path.join(records_dir, new_filename)
                
                # Copy the file
                shutil.copy2(record['file_path'], new_file_path)
                logging.info(f"Copied file to: {new_file_path}")
                
                # Update record with new filename and path
                records_df.at[index, 'new_filename'] = new_filename
                records_df.at[index, 'file_path'] = new_file_path
                
                # Update checksums
                if record['checksum'] in processed_checksums:
                    processed_checksums[record['checksum']]['processed_file'] = new_filename
            except Exception as e:
                logging.error(f"Error creating filename for record {index}: {str(e)}")
        
        # Save checksums
        if checksums_file:
            save_processed_checksums(checksums_file, processed_checksums)
        
        # Format data for CSV
        csv_df = records_df.copy()
        for col in ['diagnoses', 'treatments', 'medications']:
            if col in csv_df.columns:
                csv_df[col] = csv_df[col].apply(lambda x: '; '.join(x) if isinstance(x, list) else x)
        
        # Save CSV
        csv_path = os.path.join(output_location, 'data_files', 'extracted_data.csv')
        csv_df.to_csv(csv_path, index=False)
        logging.info(f"Saved data to CSV: {csv_path}")
        
        # Generate HTML
        output_html = config.get('output_html', 'output.html')
        output_html_path = os.path.join(output_location, output_html)
        create_html_page(records_df.to_dict('records'), output_html_path)
        logging.info(f"Created HTML output at: {output_html_path}")
        
        logging.info("Processing complete")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

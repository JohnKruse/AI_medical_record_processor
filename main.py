import os
import sys
import yaml
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime as dt  # Renaming the import to avoid conflicts
from typing import Dict, Any  # Importing Dict and Any for type hinting
import json  # Add this at the top with other imports
import pandas as pd
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
    
    logging.info(f"Loaded configuration from {config_path}")
    logging.info(f"Skip processed files: {config['skip_processed_files']} (type: {type(config['skip_processed_files'])})")
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
    skip_processed = config['skip_processed_files']  # Use exact value from config
    skip_process_review_interval = config.get('skip_process_review_interval', 180)  # Default to 180 days
    checksums_file = os.path.join(output_location, 'data_files', 'processed_files.json')
    
    logging.info(f"Processing settings: skip_processed={skip_processed}, review_interval={skip_process_review_interval} days")
    logging.info(f"Using checksums file: {checksums_file}")
    
    records = []
    previous_file = None

    # Load existing checksums if skipping processed files
    processed_checksums = load_processed_checksums(checksums_file) if skip_processed else {}
    logging.info(f"Loaded {len(processed_checksums)} processed file checksums")

    # Get the current datetime once
    current_datetime = dt.now()
    current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

    # Retrieve the OpenAI API key once at the start
    openai_api_key = os.getenv('OPENAI_API_KEY') or config.get('OPENAI_API_KEY')
    if openai_api_key is None:
        logging.error("OpenAI API Key is not set.")
    else:
        logging.info(f"OpenAI API Key: {openai_api_key[:15]}")

    # Check for files in scans directory
    files_found = False
    all_files = []
    for root, dirs, files in os.walk(scans_location):
        if files:
            files_found = True
            for file in sorted(files):
                if not file.startswith('.'):  # Skip dot files
                    all_files.append((root, file))
    
    if files_found:
        total_files = len(all_files)
        print(f"\nFound {total_files} files to process")
        
        for idx, (root, file) in enumerate(all_files, 1):
            print(f"\nProcessing file {idx} / {total_files}: {file}")
            file_path = os.path.join(root, file)
            
            # Calculate checksum
            file_checksum = calculate_checksum(file_path)
            
            # Check if file was previously processed
            if file_checksum in processed_checksums:
                last_processed_str = processed_checksums[file_checksum].get('processed_date')
                if last_processed_str:
                    try:
                        last_processed = dt.strptime(last_processed_str, '%Y-%m-%d %H:%M:%S')
                        days_since_processed = (current_datetime - last_processed).days
                        
                        if skip_processed:
                            if days_since_processed < skip_process_review_interval:
                                print(f"Skipping file processed {days_since_processed} days ago: {file}")
                                continue
                            else:
                                print(f"File was processed {days_since_processed} days ago (> {skip_process_review_interval} days). Reprocessing: {file}")
                        else:
                            print(f"File exists but skip_processed is False. Processing: {file}")
                    except ValueError as e:
                        logging.error(f"Error parsing last processed date: {str(e)}")
                        print(f"Error with last processed date. Processing: {file}")
                else:
                    print(f"File exists but no process date found. Processing: {file}")
            else:
                print(f"New file. Processing: {file}")

            try:
                # Process file and extract text
                text = process_file(file_path, config, openai_api_key)
                print("Successfully extracted text")

                # Extract treatment date from text using first date found
                treatment_date = find_first_date_in_text(text)
                if treatment_date:
                    metadata = {'date_of_origin': dt.strptime(treatment_date, '%Y-%m-%d')}
                else:
                    metadata = {}
                logging.info(f"Using metadata for filename: {metadata}")

                # Create initial record without filename
                record = {
                    'file_path': file_path,
                    'original_filename': file,
                    'checksum': file_checksum,
                    'text': text,
                    'primary_condition': '',
                    'diagnoses': [],
                    'treatments': [],
                    'medications': [],
                    'test_results': [],
                    'visit_type': '',
                    'provider_name': '',
                    'provider_facility': '',
                    'summary': '',
                    'treatment_date': treatment_date,
                    'last_processed': current_datetime_str
                }

                # Update processed checksums using the current datetime
                processed_checksums[file_checksum] = {
                    'original_file': file,
                    'processed_date': current_datetime_str
                }
                
                # Save checksums after each file is processed
                save_processed_checksums(checksums_file, processed_checksums)

                # Add record to list for AI processing
                records.append(record)

            except Exception as e:
                logging.error(f"Error processing {file}: {str(e)}")
                continue

    if not files_found:
        logging.warning(f"No files found in scans directory: {scans_location}")

    print(f"\nSuccessfully processed {len(records)} files")
    return records, processed_checksums, checksums_file, openai_api_key

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
        'last_processed': current_datetime  # New column for processing timestamp
    }
    
    for col, default_value in new_columns.items():
        if col not in records_df.columns:
            records_df[col] = default_value
    
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
        
        # Process all files and get the API key
        records, processed_checksums, checksums_file, openai_api_key = process_files(config)
        
        if records:
            # Save checksums to data_files directory
            checksums_file = os.path.join(config['output_location'], 'data_files', 'processed_files.json')
            save_processed_checksums(checksums_file, processed_checksums)
            
            # Convert records to DataFrame for AI processing
            records_df = pd.DataFrame(records)
            logging.info(f"DataFrame before saving: {records_df.info()}")
            
            # Process records through AI
            logging.info("Processing records - batch_process_medical_records")
            records_df = batch_process_medical_records(
                records_df=records_df,
                config=config,
                openai_api_key=openai_api_key
            )
            
            # Now create filenames and copy files after AI processing
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
                    processed_checksums[record['checksum']]['processed_file'] = new_filename
                except Exception as e:
                    logging.error(f"Error creating filename for record {index}: {str(e)}")
            
            # Create output files in their respective directories
            html_path = os.path.join(output_location, config.get('output_html', 'output.html'))
            csv_path = os.path.join(output_location, 'data_files', 'extracted_data.csv')
            
            # Log DataFrame info before saving
            logging.info("DataFrame columns before saving:")
            for col in records_df.columns:
                logging.info(f"Column: {col}")
            
            # Format lists for CSV
            for col in ['diagnoses', 'treatments', 'medications']:
                records_df[col] = records_df[col].apply(lambda x: '; '.join(x) if isinstance(x, list) else x)
            
            # Format test results with more detail
            def format_test_result(x):
                if not isinstance(x, list):
                    return x
                formatted_tests = []
                for test in x:
                    if isinstance(test, dict):
                        test_str = f"{test.get('name', '')}: {test.get('value', '')}"
                        if test.get('interpretation'):
                            test_str += f" - {test['interpretation']}"
                        formatted_tests.append(test_str)
                    else:
                        formatted_tests.append(str(test))
                return '; '.join(formatted_tests)
            
            records_df['test_results'] = records_df['test_results'].apply(format_test_result)
            
            # Save directly to CSV
            records_df.to_csv(csv_path, index=False)
            logging.info(f"Saved extracted data to CSV: {csv_path}")
            
            # Create HTML from records
            create_html_page(records_df.to_dict('records'), html_path)
            
            logging.info(f"Processing complete. Processed {len(records)} files.")
        else:
            logging.warning("No files were processed")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

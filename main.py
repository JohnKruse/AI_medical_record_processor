import os
import sys
import yaml
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime as dt
from typing import Dict, Any
import json
import pandas as pd
from translator import Translator
import shutil
from pdf_generator import generate_medical_records_pdf, generate_overall_summary_pdf

from ai_utils import *
from checksum_utils import *
from file_processing import *
from metadata import find_first_date_in_text, create_new_filename
from document_utils import *

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    log_filename = os.path.join(os.path.dirname(__file__), 'medical_rec_process.log')
    handler = RotatingFileHandler(
        log_filename,
        maxBytes=250000,
        backupCount=2
    )
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logging.info("=" * 80)
    logging.info("NEW RUN STARTING " + "=" * 63)
    logging.info("=" * 80)
    logging.info("Starting medical records processing")

def substitute_config_variables(config_dict, translator=None):
    if not isinstance(config_dict, dict):
        return config_dict
    if translator is None:
        translator = Translator(os.path.join(os.path.dirname(__file__), 'translations'))
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
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    if 'skip_processed_files' in config:
        if isinstance(config['skip_processed_files'], str):
            config['skip_processed_files'] = config['skip_processed_files'].lower() == 'true'
    config = substitute_config_variables(config)
    logging.info(f"Loaded configuration from {config_path}")
    logging.info(f"Skip processed files: {config['skip_processed_files']} (type: {type(config['skip_processed_files'])})")
    if 'ai_processing' in config and 'role_prompt' in config['ai_processing']:
        logging.info(f"Role prompt after substitution: {config['ai_processing']['role_prompt']}")
    return config

def ensure_directories(config):
    scans_location = config['scans_location']
    output_location = config['output_location']
    if not os.path.exists(scans_location):
        logging.info(f"Creating scans directory: {scans_location}")
        os.makedirs(scans_location, exist_ok=True)
    if not os.path.exists(output_location):
        logging.info(f"Creating output directory: {output_location}")
        os.makedirs(output_location, exist_ok=True)
    return scans_location, output_location

def ensure_output_location(config):
    output_location = config['output_location']
    os.makedirs(output_location, exist_ok=True)
    os.makedirs(os.path.join(output_location, 'html'), exist_ok=True)
    os.makedirs(os.path.join(output_location, 'records'), exist_ok=True)
    os.makedirs(os.path.join(output_location, 'data_files'), exist_ok=True)
    web_page_dir = os.path.join(os.path.dirname(__file__), 'web_page')
    output_html_dir = os.path.join(output_location, 'html')
    logo_target = os.path.join(output_html_dir, 'Logo.png')
    if not os.path.exists(logo_target):
        shutil.copy2(
            os.path.join(web_page_dir, 'Logo.png'),
            logo_target
        )
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

def process_files(config):
    scans_location, output_location = ensure_directories(config)
    ensure_output_location(config)
    output_html = config.get('output_html', 'output.html')
    skip_processed = config['skip_processed_files']
    skip_process_review_interval = config.get('skip_process_review_interval', 180)
    checksums_file = os.path.join(output_location, 'data_files', 'processed_files.json')
    extracted_data_file = os.path.join(output_location, 'data_files', 'extracted_data.csv')
    logging.info(f"Processing settings: skip_processed={skip_processed}, review_interval={skip_process_review_interval} days")
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
    openai_api_key = os.getenv('OPENAI_API_KEY') or config.get('OPENAI_API_KEY')
    if not openai_api_key:
        raise ValueError("OpenAI API Key is not set")
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
                    text = process_file(file_path, config, openai_api_key)
                    if not text:
                        continue
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
    all_records = existing_records + new_records
    if not all_records:
        logging.warning("No records to process")
        return [], processed_checksums, checksums_file, openai_api_key
    if new_records:
        new_records_df = pd.DataFrame(new_records)
        processed_new_df = batch_process_medical_records(new_records_df, config, openai_api_key)
        if existing_records:
            existing_df = pd.DataFrame(existing_records)
            records_df = pd.concat([existing_df, processed_new_df], ignore_index=True)
        else:
            records_df = processed_new_df
    else:
        records_df = pd.DataFrame(existing_records)
    return records_df.to_dict('records'), processed_checksums, checksums_file, openai_api_key

def batch_process_medical_records(records_df: pd.DataFrame, config: Dict[str, Any], openai_api_key: str) -> pd.DataFrame:
    logging.info("Starting batch_process_medical_records")
    logging.info(f"Batch processing medical records with DataFrame of size: {len(records_df)}")
    print(f"\nProcessing {len(records_df)} records through AI analysis...")
    current_datetime = dt.now().strftime('%Y-%m-%d %H:%M:%S')
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
        'ai_treatment_date': None,
        'last_processed': current_datetime,
        'patient_first_name': '',
        'patient_middle_name': '',
        'patient_last_name': ''
    }
    for col, default_value in new_columns.items():
        if col not in records_df.columns:
            if isinstance(default_value, list):
                records_df[col] = [[] for _ in range(len(records_df))]
            else:
                records_df[col] = pd.Series([default_value] * len(records_df))
    records_df['treatment_date'] = records_df['text'].apply(find_first_date_in_text)
    logging.info("Extracted treatment dates from text")
    role_prompt = config['ai_processing']['role_prompt']
    model_name = config['ai_processing']['model_name']
    max_tokens = config['ai_processing']['max_tokens']
    temperature = config['ai_processing']['temperature']
    function_schema = config['ai_processing'].get('function_schema', None)
    logging.info(f"Function schema: {json.dumps(function_schema, indent=2)}")
    analysis_question = "Analyze this medical record and provide structured information including a summary of the visit/examination."
    for index, record in records_df.iterrows():
        print(f"\nAnalyzing record {index + 1} / {len(records_df)}: {record['original_filename']}")
        logging.debug(f"Processing record at index {index}: {record['file_path']}")
        text = record['text']
        file_path = record['file_path']
        if text:
            try:
                print("Extracting medical information...")
                logging.debug(f"Calling AI API with text: {text[:50]}...")
                ai_response = query_openai_gptX_with_schema(
                    text=text,
                    questions=[analysis_question],
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
                response_text = ai_response.get(analysis_question, '{}')
                try:
                    parsed_response = json.loads(response_text)
                    logging.debug(f"Parsed response: {parsed_response}")
                    records_df.at[index, 'primary_condition'] = parsed_response.get('primary_condition', '')
                    records_df.at[index, 'diagnoses'] = parsed_response.get('diagnoses', [])
                    records_df.at[index, 'treatments'] = parsed_response.get('treatments', [])
                    summary = parsed_response.get('summary', '')
                    records_df.at[index, 'summary'] = summary
                    records_df.at[index, 'visit_type'] = parsed_response.get('visit_type', '')
                    provider = parsed_response.get('provider', {})
                    records_df.at[index, 'provider_name'] = provider.get('name', '')
                    records_df.at[index, 'provider_facility'] = provider.get('facility', '')
                    patient = parsed_response.get('patient', {})
                    records_df.at[index, 'patient_first_name'] = patient.get('first_name', '')
                    records_df.at[index, 'patient_middle_name'] = patient.get('middle_name', '')
                    records_df.at[index, 'patient_last_name'] = patient.get('last_name', '')
                    ai_date = parsed_response.get('treatment_date', '')
                    records_df.at[index, 'ai_treatment_date'] = ai_date
                    if pd.isna(records_df.at[index, 'treatment_date']) and ai_date:
                        records_df.at[index, 'treatment_date'] = ai_date
                        logging.info(f"Using AI-extracted date: {ai_date}")
                    medications = parsed_response.get('medications', [])
                    med_list = []
                    for med in medications:
                        if isinstance(med, dict) and 'name' in med:
                            med_info = f"{med['name']}"
                            if 'dosage' in med:
                                med_info += f" ({med['dosage']})"
                            med_list.append(med_info)
                    records_df.at[index, 'medications'] = med_list
                    test_results = parsed_response.get('test_results', [])
                    if isinstance(test_results, dict):
                        test_results = [test_results]
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
                    logging.error(f"Failed to parse JSON response: {e}")
                    for col, default_value in new_columns.items():
                        records_df.at[index, col] = default_value
            except Exception as e:
                logging.error(f"Error processing text: {str(e)}")
                raise
        else:
            logging.warning(f"No text found for record at index {index}, sending file to API")
            try:
                ai_response = query_openai_gptX_with_schema(
                    text=None,
                    questions=[analysis_question],
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
                    records_df.at[index, 'primary_condition'] = parsed_response.get('primary_condition', '')
                    records_df.at[index, 'diagnoses'] = parsed_response.get('diagnoses', [])
                    records_df.at[index, 'treatments'] = parsed_response.get('treatments', [])
                    summary = parsed_response.get('summary', '')
                    records_df.at[index, 'summary'] = summary
                    records_df.at[index, 'visit_type'] = parsed_response.get('visit_type', '')
                    provider = parsed_response.get('provider', {})
                    records_df.at[index, 'provider_name'] = provider.get('name', '')
                    records_df.at[index, 'provider_facility'] = provider.get('facility', '')
                    patient = parsed_response.get('patient', {})
                    records_df.at[index, 'patient_first_name'] = patient.get('first_name', '')
                    records_df.at[index, 'patient_middle_name'] = patient.get('middle_name', '')
                    records_df.at[index, 'patient_last_name'] = patient.get('last_name', '')
                    ai_date = parsed_response.get('treatment_date', '')
                    records_df.at[index, 'ai_treatment_date'] = ai_date
                    if pd.isna(records_df.at[index, 'treatment_date']) and ai_date:
                        records_df.at[index, 'treatment_date'] = ai_date
                        logging.info(f"Using AI-extracted date: {ai_date}")
                    medications = parsed_response.get('medications', [])
                    med_list = []
                    for med in medications:
                        if isinstance(med, dict) and 'name' in med:
                            med_info = f"{med['name']}"
                            if 'dosage' in med:
                                med_info += f" ({med['dosage']})"
                            med_list.append(med_info)
                    records_df.at[index, 'medications'] = med_list
                    test_results = parsed_response.get('test_results', [])
                    if isinstance(test_results, dict):
                        test_results = [test_results]
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
                    logging.error(f"Failed to parse JSON response: {e}")
                    for col, default_value in new_columns.items():
                        records_df.at[index, col] = default_value
            except Exception as e:
                logging.error(f"Error processing file: {str(e)}")
                for col, default_value in new_columns.items():
                    records_df.at[index, col] = default_value
    print("\nAI analysis complete for all records")
    return records_df

def generate_overall_summary(records_df: pd.DataFrame, config: Dict[str, Any], openai_api_key: str) -> Dict[str, Any]:
    logging.info("Generating overall medical history summary")
    records_df = records_df.sort_values('treatment_date', ascending=True)
    history_text = []
    for _, record in records_df.iterrows():
        visit_date = record.get('treatment_date', 'Unknown Date')
        visit_type = record.get('visit_type', 'Unknown Visit Type')
        provider = record.get('provider_name', 'Unknown Provider')
        diagnoses = record.get('diagnoses', [])
        treatments = record.get('treatments', [])
        medications = record.get('medications', [])
        summary = record.get('summary', '')
        visit_text = f"""
        Date: {visit_date}
        Visit Type: {visit_type}
        Provider: {provider}
        Diagnoses: {', '.join(diagnoses) if isinstance(diagnoses, list) else diagnoses}
        Treatments: {', '.join(treatments) if isinstance(treatments, list) else treatments}
        Medications: {', '.join(medications) if isinstance(medications, list) else medications}
        Summary: {summary}
        """
        history_text.append(visit_text)
    combined_history = "\n\n".join(history_text)
    ai_config = config.get('ai_overall_summary', {})
    model_name = ai_config.get('model_name', 'gpt-4o-mini')
    role_prompt = ai_config.get('role_prompt', '')
    max_tokens = ai_config.get('max_tokens', 10000)
    temperature = ai_config.get('temperature', 0.1)
    function_schema = ai_config.get('function_schema', {})
    analysis_question = "Generate a comprehensive medical history summary based on all visits and records."
    try:
        ai_response = query_openai_gptX_with_schema(
            text=combined_history,
            questions=[analysis_question],
            role_prompt=role_prompt,
            model_name=model_name,
            api_key=openai_api_key,
            file_path=None,
            function_schema=function_schema,
            max_tokens=max_tokens,
            temperature=temperature
        )
        response_text = ai_response.get(analysis_question, '{}')
        summary_data = json.loads(response_text)
        logging.info("Successfully generated overall medical history summary")
        return summary_data
    except Exception as e:
        logging.error(f"Error generating overall summary: {str(e)}")
        return {
            "patient": {"description": "Error generating patient description"},
            "medical_history": "Error generating medical history summary"
        }

def main():
    setup_logging()
    try:
        logging.info("Loading configuration")
        config = load_config('config/config.yaml')

        # Cleanup at start of run
        output_location = config['output_location']
        logging.info("Cleaning up previous output files")
        cleanup_paths = [
            os.path.join(output_location, 'data_files'),
            os.path.join(output_location, 'records'),
            os.path.join(output_location, config.get('output_html', 'output.html')),
            os.path.join(output_location, config.get('output_pdf', 'medical_records_output.pdf'))
        ]
        for path in cleanup_paths:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    logging.info(f"Removed directory: {path}")
                else:
                    os.remove(path)
                    logging.info(f"Removed file: {path}")

        ensure_output_location(config)
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
        records_df = pd.DataFrame(records)

        output_location = config['output_location']
        records_dir = os.path.join(output_location, 'records')

        for index, record in records_df.iterrows():
            try:
                new_filename = create_new_filename({}, record.to_dict(), config)
                ext = os.path.splitext(record['original_filename'])[1]
                new_filename = f"{new_filename}{ext}"
                new_file_path = os.path.join(records_dir, new_filename)
                shutil.copy2(record['file_path'], new_file_path)
                logging.info(f"Copied file to: {new_file_path}")
                records_df.at[index, 'new_filename'] = new_filename
                records_df.at[index, 'file_path'] = new_file_path
                if record['checksum'] in processed_checksums:
                    processed_checksums[record['checksum']]['processed_file'] = new_filename
            except Exception as e:
                logging.error(f"Error creating filename for record {index}: {str(e)}")

        if checksums_file:
            save_processed_checksums(checksums_file, processed_checksums)

        csv_df = records_df.copy()
        for col in ['diagnoses', 'treatments', 'medications']:
            if col in csv_df.columns:
                csv_df[col] = csv_df[col].apply(lambda x: '; '.join(x) if isinstance(x, list) else x)

        overall_summary = generate_overall_summary(records_df, config, openai_api_key)
        logging.info("Generated overall patient summary")

        summary_path = os.path.join(output_location, 'data_files', 'overall_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(overall_summary, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved overall summary to: {summary_path}")

        # Use output_short_summary_pdf from config, place in output dir
        current_date = dt.now().strftime('%Y%m%d')
        summary_pdf_name = config.get('output_short_summary_pdf', f'overall_summary_{current_date}.pdf')
        summary_pdf_path = os.path.join(output_location, summary_pdf_name)
        generate_overall_summary_pdf(config, summary_pdf_path)
        logging.info(f"Generated overall summary PDF: {summary_pdf_path}")

        # Add summary record (unchanged functionality)
        summary_record = {
            'treatment_date': dt.now().strftime('%Y-%m-%d'),
            'visit_type': 'Overall Summary',
            'provider_name': 'Medical Records System',
            'diagnoses': [],
            'treatments': [],
            'medications': [],
            'primary_condition': 'Patient Summary Report',
            'file_path': summary_pdf_path,
            'new_filename': os.path.basename(summary_pdf_path),
            'original_filename': os.path.basename(summary_pdf_path),
            'checksum': '',
            'notes': 'Automatically generated summary of all medical records'
        }
        records_df = pd.concat([pd.DataFrame([summary_record]), records_df], ignore_index=True)

        # Update CSV with final records
        csv_df = records_df.copy()
        for col in ['diagnoses', 'treatments', 'medications']:
            if col in csv_df.columns:
                csv_df[col] = csv_df[col].apply(lambda x: '; '.join(x) if isinstance(x, list) else x)
        csv_path = os.path.join(output_location, 'data_files', 'extracted_data.csv')
        csv_df.to_csv(csv_path, index=False)
        logging.info(f"Saved data to CSV: {csv_path}")

        # Re-generate HTML after adding summary record
        output_html = config.get('output_html', 'output.html')
        output_html_path = os.path.join(output_location, output_html)
        create_html_page(records_df.to_dict('records'), output_html_path, overall_summary)
        logging.info(f"Created HTML output at: {output_html_path}")

        # Now rename all records except the summary PDF record again
        # We already renamed normal records above, but summary PDF was just added.
        # Attempt to rename the summary PDF would place it into records_dir.
        # We must skip that to keep it in output dir as requested.
        # Additive change: skip copying for the 'Overall Summary' record:
        for index, record in records_df.iterrows():
            if record.get('visit_type') == 'Overall Summary':
                # Skip re-processing this record to keep summary PDF in output dir
                continue
            # For others, if needed, ensure they are properly named and placed. They already are.

        logging.info("Processing complete")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
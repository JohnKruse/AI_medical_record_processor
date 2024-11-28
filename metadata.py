import os
import re
import datetime
from dateutil import parser
import logging
import glob

def extract_metadata(file_path):
    """Extract metadata from file."""
    stats = os.stat(file_path)
    metadata = {
        'file_creation_date': datetime.datetime.fromtimestamp(stats.st_ctime),
        'file_modification_date': datetime.datetime.fromtimestamp(stats.st_mtime),
        'file_size': stats.st_size,
        'original_file': file_path
    }
    logging.info(f"Extracted metadata for: {file_path}")
    return metadata

def find_date_in_text(text):
    """Find date within extracted text."""
    date_patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # Matches dates like dd/mm/yyyy or dd/mm/yy
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',    # Matches dates like yyyy-mm-dd
    ]
    min_valid_year = 2005  # Ignore dates before 2005
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            for match in matches:
                try:
                    date = parser.parse(match, dayfirst=True)
                    # Only return dates from 2005 onwards
                    if date.year >= min_valid_year:
                        logging.info(f"Found valid date in text: {date}")
                        return date
                except ValueError:
                    continue
    logging.info("No valid date found in text")
    return None

def find_earliest_date_in_text(text):
    """Find earliest date within extracted text after 2005-01-01."""
    if not text:
        logging.info("Empty text provided")
        return None
        
    logging.info(f"Searching for dates in text: {text[:200]}...")
    
    # First try to parse the entire text for dates
    try:
        # Try to find dates in the format "Month Day, Year"
        matches = re.findall(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', text)
        if matches:
            logging.info(f"Found word-based dates: {matches}")
            for match in matches:
                try:
                    date = parser.parse(match)
                    if date >= datetime.datetime(2005, 1, 1):
                        logging.info(f"Found valid word-based date: {date}")
                        return date.strftime('%Y-%m-%d')
                except ValueError as e:
                    logging.debug(f"Failed to parse word-based date {match}: {str(e)}")
    except Exception as e:
        logging.debug(f"Error parsing word-based dates: {str(e)}")
    
    # Then try numeric patterns
    date_patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # Matches dates like dd/mm/yyyy or dd/mm/yy
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',    # Matches dates like yyyy-mm-dd
        r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',  # Matches dates like dd-mm-yyyy
        r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b',  # Matches dates like dd.mm.yyyy
        r'\b\d{2}/\d{2}/\d{4}\b',        # Matches dates like 24/10/2024
        r'\b\d{2}\.\d{2}\.\d{4}\b',      # Matches dates like 24.10.2024
        r'\b\d{2}/\d{2}/\d{2}\b',        # Matches dates like 24/10/24
        r'\b\d{1,2}/\d{2}/\d{4}\b',      # Matches dates like 7/10/2024
        r'\b\d{2}/\d{1,2}/\d{4}\b',      # Matches dates like 24/7/2024
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',    # Matches dates like 7/7/2024
        r'\b\d{1,2}/\d{1,2}/\d{2}\b',    # Matches dates like 7/7/24
        r'\b\d{2}\s*[/-]\s*\d{2}\s*[/-]\s*\d{4}\b',  # Matches dates with optional spaces
    ]
    min_valid_date = datetime.datetime(2005, 1, 1)
    earliest_date = None
    
    # First, let's find all potential dates
    all_matches = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            all_matches.extend(matches)
            logging.info(f"Found date matches for pattern {pattern}: {matches}")
    
    logging.info(f"Total matches found: {len(all_matches)}")
    
    # Then try to parse each match
    for match in all_matches:
        try:
            # Clean up the match by removing extra spaces
            match = re.sub(r'\s+', '', match)
            date = parser.parse(match, dayfirst=True)
            logging.info(f"Parsed date: {date} from match: {match}")
            
            # Only consider dates from 2005 onwards
            if date >= min_valid_date:
                if earliest_date is None or date < earliest_date:
                    earliest_date = date
                    logging.info(f"New earliest date found: {earliest_date}")
                else:
                    logging.debug(f"Date {date} is not earlier than current earliest {earliest_date}")
            else:
                logging.debug(f"Date {date} is before {min_valid_date}, ignoring")
        except ValueError as e:
            logging.debug(f"Failed to parse date {match}: {str(e)}")
            continue
    
    if earliest_date:
        result = earliest_date.strftime('%Y-%m-%d')
        logging.info(f"Found earliest valid date in text: {result}")
        return result
    
    logging.info("No valid date found in text")
    return None

def find_first_date_in_text(text):
    """Find first valid date within extracted text after 2015."""
    if not text:
        logging.info("Empty text provided")
        return None
        
    logging.info(f"Searching for first date after 2015 in text: {text[:200]}...")
    
    # First try to parse dates in the format "Month Day, Year"
    try:
        # Try to find dates in the format "Month Day, Year"
        matches = re.findall(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', text)
        if matches:
            logging.info(f"Found word-based date: {matches[0]}")
            try:
                date = parser.parse(matches[0])
                if date.year >= 2015:
                    logging.info(f"Found valid word-based date after 2015: {date}")
                    return date.strftime('%Y-%m-%d')
            except ValueError as e:
                logging.debug(f"Failed to parse word-based date {matches[0]}: {str(e)}")
    except Exception as e:
        logging.debug(f"Error parsing word-based dates: {str(e)}")
    
    # Then try numeric patterns
    date_patterns = [
        r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # Matches dates like dd/mm/yyyy or dd/mm/yy
        r'\b\d{4}-\d{1,2}-\d{1,2}\b',    # Matches dates like yyyy-mm-dd
        r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',  # Matches dates like dd-mm-yyyy
        r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b',  # Matches dates like dd.mm.yyyy
        r'\b\d{2}/\d{2}/\d{4}\b',        # Matches dates like 24/10/2024
        r'\b\d{2}\.\d{2}\.\d{4}\b',      # Matches dates like 24.10.2024
        r'\b\d{2}/\d{2}/\d{2}\b',        # Matches dates like 24/10/24
        r'\b\d{1,2}/\d{2}/\d{4}\b',      # Matches dates like 7/10/2024
        r'\b\d{2}/\d{1,2}/\d{4}\b',      # Matches dates like 24/7/2024
        r'\b\d{1,2}/\d{1,2}/\d{4}\b',    # Matches dates like 7/7/2024
        r'\b\d{1,2}/\d{1,2}/\d{2}\b',    # Matches dates like 7/7/24
        r'\b\d{2}\s*[/-]\s*\d{2}\s*[/-]\s*\d{4}\b',  # Matches dates with optional spaces
    ]
    
    # Try each pattern and return the first valid date found after 2015
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        if matches:
            for match in matches:
                try:
                    # Clean up the match by removing extra spaces
                    match = re.sub(r'\s+', '', match)
                    date = parser.parse(match, dayfirst=True)
                    if date.year >= 2015:
                        logging.info(f"Found valid date after 2015: {date}")
                        return date.strftime('%Y-%m-%d')
                except ValueError as e:
                    logging.debug(f"Failed to parse date {match}: {str(e)}")
                    continue
    
    logging.info("No valid date after 2015 found in text")
    return None

def standardize_date(date):
    """Convert date to YYYY-MM-DD format."""
    return date.strftime('%Y-%m-%d')

def get_next_sequence_number(output_dir, date_str):
    """Get the next available sequence number for a given date."""
    # Look for existing files with the same date
    pattern = os.path.join(output_dir, f"{date_str}_*")
    existing_files = glob.glob(pattern)
    
    # Extract sequence numbers from existing files
    sequence_numbers = []
    seq_pattern = re.compile(r'_(\d{3})$')
    
    for file in existing_files:
        match = seq_pattern.search(os.path.splitext(file)[0])
        if match:
            sequence_numbers.append(int(match.group(1)))
    
    # If no existing files, start with 1, otherwise use max + 1
    next_seq = 1 if not sequence_numbers else max(sequence_numbers) + 1
    logging.info(f"Next sequence number for {date_str}: {next_seq:03d}")
    return next_seq

def create_new_filename(metadata, record_data, config):
    """Create a new filename based on treatment date, visit type, and provider name."""
    # Get treatment date
    treatment_date = record_data.get('treatment_date')
    if not treatment_date:
        treatment_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Get visit type, convert to lowercase and replace spaces with underscores
    visit_type = record_data.get('visit_type', 'unknown')
    visit_type = visit_type.lower().replace(' ', '_')
    
    # Get provider name and extract last word
    provider_name = record_data.get('provider_name', '')
    provider_name_last = provider_name.split()[-1] if provider_name else 'unknown'
    provider_name_last = provider_name_last.lower()
    
    # Get the output directory from config
    output_dir = config['output_location']
    
    # Get next sequence number for this date
    seq_num = get_next_sequence_number(output_dir, treatment_date)
    
    # Format the filename
    filename_format = config.get('filename_format', '{treatment_date}_{visit_type}_{provider_name_last}_{seq:03d}')
    new_filename = filename_format.format(
        treatment_date=treatment_date,
        visit_type=visit_type,
        provider_name_last=provider_name_last,
        seq=seq_num
    )
    
    logging.info(f"Created new filename: {new_filename}")
    return new_filename

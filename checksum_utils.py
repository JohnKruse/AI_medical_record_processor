import json
import hashlib
import logging

def calculate_checksum(file_path):
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read the file in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_processed_checksums(checksums_file):
    """Load previously processed file checksums."""
    try:
        with open(checksums_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.info("No existing checksums file found, starting fresh")
        return {}

def save_processed_checksums(checksums_file, checksums):
    """Save processed file checksums."""
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f, indent=2)
    logging.info(f"Saved {len(checksums)} checksums to {checksums_file}")

# Medical Records Processing System

A comprehensive Python-based system for processing, analyzing, and managing medical records using AI. This system leverages OpenAI's GPT models to extract and analyze information from medical documents, providing structured outputs and a web-based interface for easy access and review.

## Key Features

- **Document Processing**
  - Support for multiple document formats (PDF, TXT, DOCX)
  - OCR capabilities for scanned documents using Tesseract
  - Smart file path handling and checksum verification
  - Automatic file organization and renaming
  
- **AI-Powered Analysis**
  - Integration with OpenAI's GPT-4 models
  - Structured medical data extraction
  - Intelligent date and provider detection
  - Multi-language medical terminology processing
  
- **Data Management**
  - Structured data output (CSV, JSON)
  - Secure document handling with checksums
  - Incremental processing with skip functionality
  - Automated metadata extraction
  
- **PDF Generation**
  - Comprehensive medical record PDFs
  - Short summary reports
  - Table of contents generation
  - Original document preservation
  
- **Web Interface**
  - Interactive document viewer
  - Chronological record organization
  - Print functionality
  - Keyboard navigation
  
- **Internationalization**
  - Multi-language support (English, Italian)
  - Dynamic translation management
  - Language-specific formatting

## System Requirements

- Python 3.8 or higher
- OpenAI API key
- Tesseract OCR engine
- Sufficient storage for document processing
- Internet connection for AI processing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/medical_records_2024.git
cd medical_records_2024
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the system:
   - Copy `config/config.template.yaml` to `config/config.yaml`
   - Set your OpenAI API key in environment:
     ```bash
     export OPENAI_API_KEY='your-api-key'
     ```
   - Adjust paths and processing parameters in config.yaml

## Project Structure

```
medical_records_2024/
├── config/                 # Configuration files
│   ├── config.yaml        # Main configuration
│   └── config.template.yaml# Template configuration
├── translations/          # Language files
│   ├── en.json           # English translations
│   └── it.json           # Italian translations
├── web_page/             # Web interface assets
│   └── Logo.png          # Application logo
├── ai_utils.py           # AI processing utilities
├── checksum_utils.py     # File integrity verification
├── document_utils.py     # Document handling
├── file_processing.py    # File operations
├── main.py              # Application entry point
├── metadata.py          # Metadata management
├── openai_processor.py  # OpenAI API integration
├── pdf_generator.py     # PDF report generation
└── translation_manager.py# Translation handling
```

## Configuration

The system uses a YAML configuration file (`config.yaml`) with the following key settings:

```yaml
output_language: 'en'  # or 'it' for Italian
skip_processed_files: true
skip_process_review_interval: 180  # days
scans_location: '/path/to/input/scans'
output_location: '/path/to/output'
output_pdf: 'medical_records.pdf'
output_short_summary_pdf: 'medical_records_short_summary.pdf'
output_html: 'medical_records.html'
```

## Output Structure

The system generates several outputs:

1. **PDF Reports**
   - Complete medical records with table of contents
   - Short summary report
   - Individual record PDFs with metadata

2. **Web Interface**
   - Interactive HTML viewer
   - Chronological record listing
   - Record details and summaries

3. **Data Files**
   - Extracted data in CSV format
   - Processing metadata in JSON
   - Checksums for processed files

## Processing Features

- **Smart Skip**: Avoids reprocessing recent files
- **Incremental Updates**: Only processes new or modified files
- **Error Recovery**: Continues processing despite individual file failures
- **Logging**: Comprehensive logging with rotation

## Security Features

- Secure API key handling
- Checksum verification for file integrity
- No storage of sensitive data in logs
- Configurable file access patterns

## Dependencies

Key dependencies include:
- openai (≥1.3.0): AI processing
- PyMuPDF (≥1.23.7): PDF processing
- pytesseract (≥0.3.10): OCR capabilities
- pandas (≥2.1.3): Data handling
- PyYAML (≥6.0.1): Configuration
- reportlab (≥4.0.7): PDF generation
- PyPDF2 (≥3.0.0): PDF manipulation

## Usage

1. Place medical documents in the configured input directory
2. Run the processing script:
```bash
python main.py
```

3. Access the results:
   - View the generated HTML interface
   - Open the comprehensive PDF report
   - Check the data files for extracted information

## Error Handling

The system includes robust error handling:
- Graceful handling of OCR failures
- Fallback to alternative text extraction methods
- Detailed error logging
- Continuation despite individual file failures

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT models
- The open-source community for various dependencies
- Contributors and testers

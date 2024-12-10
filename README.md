# Medical Records Processing System

A comprehensive Python-based system for processing, analyzing, and managing medical records using AI. This system leverages OpenAI's GPT models to extract and analyze information from medical documents, providing structured outputs and a web-based interface for easy access and review.

## Key Features

- **Document Processing**
  - Support for multiple document formats (PDF, TXT, DOCX)
  - OCR capabilities for scanned documents
  - Automated text extraction and preprocessing
  
- **AI-Powered Analysis**
  - Integration with OpenAI's GPT models
  - Intelligent medical data extraction
  - Natural language processing of medical terminology
  
- **Data Management**
  - Structured data output (CSV, JSON, Excel)
  - Secure document handling
  - Automated checksum verification
  
- **Web Interface**
  - User-friendly document viewer
  - Search and filter capabilities
  - Report generation
  
- **Internationalization**
  - Multi-language support
  - Translation management
  - Template-based document generation

## System Requirements

- Python 3.8 or higher
- OpenAI API key
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
   - Set up your OpenAI API key in `.env` file
   - Adjust processing parameters as needed

## Project Structure

```
medical_records_2024/
├── config/                 # Configuration files
├── html/                  # Web interface templates
├── records/              # Storage for medical records
├── reports/              # Generated reports
├── templates/            # Document templates
├── translations/         # Language files
├── web_page/            # Web interface assets
│
├── ai_utils.py           # AI processing utilities
├── checksum_utils.py     # File integrity verification
├── document_utils.py     # Document handling
├── file_processing.py    # File operations
├── main.py              # Application entry point
├── metadata.py          # Metadata management
├── openai_processor.py  # OpenAI API integration
├── pdf_generator.py     # PDF report generation
├── template_manager.py  # Template handling
├── text_extraction.py   # Text extraction
├── translation_manager.py# Translation handling
└── translator.py        # Translation utilities
```

## Dependencies

Key dependencies include:
- python-dotenv (≥1.0.0): Environment management
- PyMuPDF (≥1.23.7): PDF processing
- pytesseract (≥0.3.10): OCR capabilities
- Pillow (≥10.1.0): Image processing
- pandas (≥2.1.3): Data manipulation
- PyYAML (≥6.0.1): Configuration management
- reportlab (≥4.0.7): PDF generation

## Quick Start

1. Place medical documents in the `records` directory
2. Run the processing script:
```bash
./run.sh
```
or
```bash
python main.py
```

3. Access the web interface to view processed records

## Configuration

The system is configured through `config.yaml`. Key configuration sections:
- Input/output paths
- AI model parameters
- Processing options
- Security settings
- Language preferences

## Security Considerations

- API keys and sensitive data are stored in `.env` files (not in version control)
- Document checksums are verified for integrity
- Processed data is stored securely
- Access controls through web interface

## Logging

The system maintains detailed logs:
- Processing activities in `medical_rec_process.log`
- Rotating log files for historical tracking
- Error and debug information

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with a clear description

Last updated: December 10, 2024

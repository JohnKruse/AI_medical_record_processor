# Medical Records Processing System

A Python-based system for processing and analyzing medical records using AI. This system extracts information from medical documents, processes them using OpenAI's GPT models, and generates structured analysis.

## Features

- Automated processing of medical records in various formats (PDF, TXT)
- Text extraction and OCR capabilities
- AI-powered analysis using OpenAI's GPT models
- Structured data output in multiple formats
- Web-based viewer for processed records
- Configurable processing pipeline

## Prerequisites

- Python 3.8+
- OpenAI API key
- Required Python packages (see `requirements.txt`)

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

3. Set up configuration:
   - Copy `config/config.template.yaml` to `config/config.yaml`
   - Update the configuration with your settings
   - Create a `.api_keys.env` file with your API keys

## Configuration

The system uses a YAML configuration file (`config/config.yaml`) for settings. A template is provided in `config/config.template.yaml`. Key configurations include:

- Input/output directories
- AI model settings
- Processing parameters
- File handling options

## Usage

1. Place medical records in the configured input directory
2. Run the processing script:
```bash
python main.py
```

3. Access processed records through the web viewer in the output directory

## Project Structure

```
medical_records_2024/
├── config/                 # Configuration files
├── ai_utils.py            # AI processing utilities
├── checksum_utils.py      # File integrity checking
├── document_utils.py      # Document handling utilities
├── file_processing.py     # File processing logic
├── main.py               # Main application entry
├── metadata.py           # Metadata extraction
├── openai_processor.py   # OpenAI API integration
└── text_extraction.py    # Text extraction utilities
```

## Security

- Sensitive configuration (API keys, paths) should be stored in environment files
- The actual configuration file (`config.yaml`) is excluded from version control
- Personal information should be handled according to relevant privacy regulations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

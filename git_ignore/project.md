# Medical Records Processing System 2024

## Project Overview
This system is designed to process and manage medical records, providing automated processing, data extraction, and web-based visualization of medical documents.

## Core Components

### 1. Main Application (`main.py`)
- Entry point for the application
- Handles configuration loading and logging setup
- Orchestrates the overall processing pipeline
- Manages batch processing of medical records

### 2. Document Processing
- **document_utils.py**: Core document handling utilities
  - HTML page generation for record visualization
  - Document summarization capabilities
  - CSV export functionality

- **text_extraction.py**: Text extraction from various document formats
- **metadata.py**: Metadata extraction and filename management
- **checksum_utils.py**: File integrity verification
- **file_processing.py**: File system operations and processing
- **openai_processor.py**: AI-powered text processing using OpenAI

### 3. Configuration
- Located in `config/` directory
- YAML-based configuration system
- Configurable paths, processing rules, and system settings

### 4. Web Interface
- Located in `html/` and `web_page/` directories
- Provides visual interface for viewing processed records
- Includes detail pages for individual records

### 5. Logging
- Rotating log files: `medical_rec_process.log`
- Debug-level logging for detailed system operations
- Automated log rotation to manage file sizes

## Project Guidelines

### Code Organization
1. Keep related functionality in dedicated modules
2. Maintain clear separation of concerns between components
3. Use type hints for better code clarity and maintainability

### Data Processing Rules
1. Always verify file integrity using checksums
2. Maintain original files unchanged
3. Generate appropriate metadata for all processed documents

### Security Considerations
1. Handle sensitive medical data with appropriate care
2. Keep API keys and sensitive configurations separate
3. Implement proper access controls for web interface

### Development Workflow
1. Document significant changes and updates in this file
2. Keep dependencies updated and documented
3. Maintain comprehensive logging for debugging
4. Test new features thoroughly before integration

## Tech Stack
### Backend
- Python 3.x
  - Core language for all processing logic
  - Type hints for enhanced code safety
- OpenAI API
  - Used for intelligent text processing
  - Document summarization
- Custom Python Libraries
  - `johns_python_libs` for utility functions
  - Local processing modules

### Data Processing
- pandas: Data manipulation and CSV handling
- YAML: Configuration management
- Logging: RotatingFileHandler for log management

### Frontend
- HTML/CSS: Static page generation
- Document visualization interface
- Detail views for individual records

## Technical Considerations & Known Issues

### Performance
1. Large File Processing
   - Memory usage during batch processing
   - Potential bottlenecks in text extraction
   - Log rotation thresholds may need adjustment

2. API Limitations
   - OpenAI API rate limits
   - Response time variations
   - Token usage optimization needed

### System Requirements
1. Disk Space
   - Log file growth
   - Processed document storage
   - Temporary file management

2. Memory Usage
   - Batch processing limitations
   - DataFrame size constraints
   - Document loading overhead

### Known Issues
1. File Processing
   - Some PDF formats may have extraction issues
   - Large files may slow down processing
   - Certain date formats may not be recognized

2. Integration Points
   - OpenAI API occasional timeout
   - Custom library dependencies
   - Configuration file versioning

### Monitoring Needs
1. System Health
   - Log file size tracking
   - Processing queue length
   - API usage metrics

2. Error Tracking
   - Failed processing attempts
   - API failures
   - Data validation issues

## Future Enhancements
- [ ] Enhance AI-based document summarization
- [ ] Implement advanced search capabilities
- [ ] Add user authentication for web interface
- [ ] Improve processing performance for large batches

## Dependencies
- Python 3.x
- OpenAI API integration
- pandas for data manipulation
- Custom utilities from johns_python_libs

## Notes
This document should be updated as the project evolves. Add new sections for:
- Major architectural decisions
- Important workflow changes
- New processing rules
- Security considerations
- Performance optimizations

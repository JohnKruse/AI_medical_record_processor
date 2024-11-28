import pytesseract
from PIL import Image
import PyPDF2
import docx
import xlrd
from pdf2image import convert_from_path
import io
import logging

def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_text_from_pdf(file_path):
    text = ''
    try:
        logging.info(f"Attempting normal text extraction from {file_path}")
        # First try normal text extraction
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(reader.pages):
                logging.info(f"Processing page {page_num + 1} with normal extraction")
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                except Exception as page_error:
                    logging.error(f"Error extracting text from page {page_num + 1}: {str(page_error)}")
        
        # If we got no text, try OCR approach
        if not text.strip():
            logging.info(f"No text found in PDF {file_path}, attempting OCR...")
            try:
                # Convert PDF to images
                logging.info("Converting PDF to images using pdf2image...")
                images = convert_from_path(file_path)
                logging.info(f"Successfully converted PDF to {len(images)} images")
                
                # Perform OCR on each image
                for i, image in enumerate(images):
                    logging.info(f"Processing page {i+1} with OCR")
                    try:
                        page_text = pytesseract.image_to_string(image)
                        if page_text and page_text.strip():
                            logging.info(f"Successfully extracted text from page {i+1}")
                            text += page_text.strip() + "\n"
                        else:
                            logging.warning(f"No text extracted from page {i+1}")
                    except Exception as ocr_page_error:
                        logging.error(f"Error during OCR on page {i+1}: {str(ocr_page_error)}")
            except Exception as ocr_error:
                logging.error(f"Error during OCR processing: {str(ocr_error)}")
                raise
        
        if not text.strip():
            logging.warning("No text could be extracted from the PDF using either method")
            return ""
            
        return text
    except Exception as e:
        logging.error(f"Error processing PDF {file_path}: {str(e)}")
        return ""

def extract_text_from_image(file_path, lang):
    image = Image.open(file_path)
    return pytesseract.image_to_string(image, lang=lang)

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return '\n'.join([para.text for para in doc.paragraphs])

def extract_text_from_excel(file_path):
    workbook = xlrd.open_workbook(file_path)
    text = ''
    for sheet in workbook.sheets():
        for row in range(sheet.nrows):
            text += ' '.join([str(cell.value) for cell in sheet.row(row)]) + '\n'
    return text

def detect_language(image, config):
    return config.get('ocr_language', 'eng+ita')

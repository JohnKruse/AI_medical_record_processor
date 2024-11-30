import os
import json
import logging
import glob

class Translator:
    def __init__(self, translations_dir):
        self.translations_dir = translations_dir
        self.language_codes = self._discover_languages()
        # Mapping between ISO 639-1 codes and Tesseract language codes
        self.tesseract_codes = {
            'en': 'eng',
            'es': 'spa',
            'de': 'deu',
            'it': 'ita'
        }
        
    def _discover_languages(self):
        """Discover available languages by scanning the translations directory."""
        languages = {}
        translation_files = glob.glob(os.path.join(self.translations_dir, "*.json"))
        
        for file_path in translation_files:
            # Skip non-language files like __init__.py
            if os.path.basename(file_path).startswith('_'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'language_name' in data:
                        lang_code = os.path.splitext(os.path.basename(file_path))[0]
                        languages[lang_code] = data['language_name']
                    else:
                        logging.warning(f"Missing language_name in {file_path}")
            except Exception as e:
                logging.error(f"Error loading translation file {file_path}: {str(e)}")
                
        if not languages:
            raise ValueError(f"No valid translation files found in {self.translations_dir}")
            
        logging.info(f"Discovered languages: {languages}")
        return languages
        
    def get_language_name(self, language_code):
        """Get the full name of a language from its code."""
        if language_code not in self.language_codes:
            available = ', '.join(sorted(self.language_codes.keys()))
            raise ValueError(f"Unsupported language code: {language_code}. Available languages: {available}")
            
        return self.language_codes[language_code]
        
    def get_tesseract_code(self, language_code):
        """Convert ISO 639-1 language code to Tesseract language code."""
        if language_code not in self.language_codes:
            available = ', '.join(sorted(self.language_codes.keys()))
            raise ValueError(f"Unsupported language code: {language_code}. Available languages: {available}")
            
        return self.tesseract_codes.get(language_code, language_code)
        
    def get_tesseract_codes(self, language_codes):
        """Convert multiple ISO 639-1 language codes to Tesseract format.
        
        Args:
            language_codes: String of '+' separated ISO codes (e.g., 'en+it')
            
        Returns:
            String of '+' separated Tesseract codes (e.g., 'eng+ita')
        """
        if not language_codes:
            return 'eng'  # Default to English
            
        codes = language_codes.split('+')
        tesseract_codes = [self.get_tesseract_code(code.strip()) for code in codes]
        return '+'.join(tesseract_codes)
        
    def load_translations(self, language_code):
        """Load translations for a specific language."""
        if language_code not in self.language_codes:
            available = ', '.join(sorted(self.language_codes.keys()))
            raise ValueError(f"Unsupported language code: {language_code}. Available languages: {available}")
            
        try:
            translation_file = os.path.join(self.translations_dir, f"{language_code}.json")
            with open(translation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading translations for {language_code}: {str(e)}")
            raise

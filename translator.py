import os
import json
import logging
import glob

class Translator:
    def __init__(self, translations_dir):
        self.translations_dir = translations_dir
        self.language_codes = self._discover_languages()
        
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

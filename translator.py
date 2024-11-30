import os
import json
import logging

class Translator:
    def __init__(self, translations_dir):
        self.translations_dir = translations_dir
        self.language_codes = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ru': 'Russian'
        }
        
    def get_language_name(self, language_code):
        """Get the full name of a language from its code."""
        return self.language_codes.get(language_code, 'English')  # Default to English if code not found
        
    def load_translations(self, language_code):
        """Load translations for a specific language."""
        try:
            translation_file = os.path.join(self.translations_dir, f"{language_code}.json")
            if not os.path.exists(translation_file):
                logging.warning(f"Translation file not found for language code: {language_code}")
                return {}
                
            with open(translation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading translations for {language_code}: {str(e)}")
            return {}

import os
import json
import logging
from typing import Dict, Any

class Translator:
    def __init__(self, translations_dir: str):
        """Initialize the translator with the translations directory."""
        self.translations_dir = translations_dir
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.load_translations()

    def load_translations(self):
        """Load all translation files from the translations directory."""
        for filename in os.listdir(self.translations_dir):
            if filename.endswith('.json'):
                language = filename[:-5]  # Remove .json extension
                file_path = os.path.join(self.translations_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[language] = json.load(f)
                    logging.info(f"Loaded translations for language: {language}")
                except Exception as e:
                    logging.error(f"Error loading translations for {language}: {str(e)}")

    def get_translation(self, key: str, language: str = 'en') -> str:
        """
        Get a translation for a key in the specified language.
        
        Args:
            key: Dot-notation key (e.g., 'fields.treatment_date')
            language: Language code (e.g., 'en', 'es', 'de', 'it')
            
        Returns:
            Translated string or the key itself if translation not found
        """
        try:
            # Default to English if requested language not available
            if language not in self.translations:
                logging.warning(f"Language {language} not found, falling back to English")
                language = 'en'

            # Navigate the nested dictionary using the dot notation
            value = self.translations[language]
            for part in key.split('.'):
                value = value[part]
            return value
        except KeyError:
            logging.warning(f"Translation key not found: {key}")
            return key
        except Exception as e:
            logging.error(f"Error getting translation: {str(e)}")
            return key

    def get_language_name(self, language_code: str, in_english: bool = True) -> str:
        """
        Get the full name of a language from its code.
        
        Args:
            language_code: Two-letter language code (e.g., 'en', 'es')
            in_english: If True, returns name in English, otherwise in native language
            
        Returns:
            Full language name or language code if not found
        """
        try:
            if language_code not in self.translations:
                logging.warning(f"Language {language_code} not found")
                return language_code
                
            metadata = self.translations[language_code].get('language_metadata', {})
            if in_english:
                return metadata.get('name_in_english', language_code)
            return metadata.get('name_in_native', language_code)
        except Exception as e:
            logging.error(f"Error getting language name: {str(e)}")
            return language_code

    def get_available_languages(self) -> list:
        """Get list of available language codes."""
        return list(self.translations.keys())

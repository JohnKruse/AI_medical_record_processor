import os
import json
import logging
from functools import lru_cache

class TranslationManager:
    def __init__(self, translations_dir, default_language='en'):
        self.translations_dir = translations_dir
        self.default_language = default_language
        self.current_language = default_language
        self._translations = {}
        self._load_translations()
    
    def _load_translations(self):
        """Load all translation files from the translations directory."""
        for filename in os.listdir(self.translations_dir):
            if filename.endswith('.json'):
                lang_code = filename.split('.')[0]
                file_path = os.path.join(self.translations_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._translations[lang_code] = json.load(f)
                except Exception as e:
                    logging.error(f"Error loading translation file {filename}: {e}")
    
    def set_language(self, language_code):
        """Set the current language."""
        if language_code in self._translations:
            self.current_language = language_code
        else:
            logging.warning(f"Language {language_code} not found, falling back to {self.default_language}")
            self.current_language = self.default_language
    
    @lru_cache(maxsize=1024)
    def get(self, key_path, language=None):
        """
        Get a translation by its dot-notation path.
        Example: manager.get('fields.treatment_date')
        """
        lang = language or self.current_language
        translation_dict = self._translations.get(lang, self._translations[self.default_language])
        
        try:
            value = translation_dict
            for key in key_path.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            # If key not found in current language, try default language
            if lang != self.default_language:
                try:
                    value = self._translations[self.default_language]
                    for key in key_path.split('.'):
                        value = value[key]
                    return value
                except (KeyError, TypeError):
                    pass
            logging.warning(f"Translation key '{key_path}' not found")
            return key_path.split('.')[-1]
    
    def get_all_languages(self):
        """Get a list of all available languages."""
        return list(self._translations.keys())
    
    def get_language_name(self, lang_code=None):
        """Get the native name of a language."""
        code = lang_code or self.current_language
        try:
            return self._translations[code]['language_metadata']['name_in_native']
        except (KeyError, TypeError):
            return code
    
    def get_all_translations(self):
        """Get all translations for the current language."""
        return self._translations.get(self.current_language, self._translations.get(self.default_language, {}))

    def to_json(self):
        """Convert current language translations to JSON for client-side use."""
        return json.dumps(self.get_all_translations())

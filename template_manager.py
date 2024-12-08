import os
import json
from string import Template

class TemplateManager:
    def __init__(self, templates_dir, translation_manager):
        self.templates_dir = templates_dir
        self.translator = translation_manager
        self._templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all template files from the templates directory."""
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.html'):
                template_name = filename.split('.')[0]
                file_path = os.path.join(self.templates_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._templates[template_name] = Template(f.read())
    
    def render(self, template_name, **kwargs):
        """
        Render a template with translations and additional context.
        Usage: template_manager.render('main', records=records, summary=summary)
        """
        if template_name not in self._templates:
            raise ValueError(f"Template {template_name} not found")
        
        # Add translations to the context
        context = {
            'tr': self.translator,
            'lang': self.translator.current_language,
            'translations_json': self.translator.to_json(),
            **kwargs
        }
        
        return self._templates[template_name].safe_substitute(context)

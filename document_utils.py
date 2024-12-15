import pandas as pd
import logging
import os
import json
import shutil
import yaml
from template_manager import TemplateManager
from translation_manager import TranslationManager

def get_document_summary(text):
    """Get document summary using AI/ML techniques."""
    # Implement actual AI/ML summary generation here
    # For now, return a placeholder summary
    logging.info("Generating document summary")
    return "Summary of the document."

def create_detail_page(record, output_dir):
    """Create an individual HTML page for a record."""
    filename = record['new_filename'].replace('.', '_') + '.html'
    detail_path = os.path.join(output_dir, 'html', 'details', filename)
    
    # Load configuration to get language
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logging.info(f"Loaded config: {config}")
    logging.info(f"Output language from config: {config.get('output_language', 'en')}")
    
    # Initialize translation manager with configured language
    translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
    translator = TranslationManager(translations_dir, default_language='en')
    translator.set_language(config.get('output_language', 'en'))
    
    # Get translations for static text
    tr = translator.get_all_translations()
    logging.info(f"Current language after setting: {translator.current_language}")
    logging.info(f"Available translations: {list(tr.keys())}")
    
    html_content = f"""<!DOCTYPE html>
<html lang="{tr['language_metadata']['code']}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{tr['page_title']} - {record['new_filename']}</title>
    <link rel="stylesheet" href="../styles.css">
    <style>
        .raw-text {{
            white-space: pre-wrap;
            font-family: monospace;
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 4px;
            max-height: 400px;
            overflow-y: auto;
        }}
    </style>
</head>
<body>
    <div class="record-details">
        <h2 class="record-title">{record['new_filename']}</h2>
        <div class="actions">
            <button class="btn btn-print" onclick="window.print()">
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M2.5 8a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
                    <path d="M5 1a2 2 0 0 0-2 2v2H2a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h1v1a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-1h1a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-1V3a2 2 0 0 0-2-2H5zM4 3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2H4V3zm1 5a2 2 0 0 0-2 2v1H2a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v-1a2 2 0 0 0-2-2H5zm7 2v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1z"/>
                </svg>
                {tr['actions']['print']}
            </button>
            <a href="../../records/{record['new_filename']}" target="_blank" class="btn">{tr['actions']['view_original']}</a>
        </div>
        <table>
            <tr><th>{tr['fields']['treatment_date_regex']}</th><td>{record.get('treatment_date', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['treatment_date_ai']}</th><td>{record.get('ai_treatment_date', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['visit_type']}</th><td>{record.get('visit_type', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['provider_name']}</th><td>{record.get('provider_name', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['provider_facility']}</th><td>{record.get('provider_facility', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['primary_condition']}</th><td>{record.get('primary_condition', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['diagnoses']}</th><td>{record.get('diagnoses', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['treatments']}</th><td>{record.get('treatments', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['medications']}</th><td>{record.get('medications', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['test_results']}</th><td>{record.get('test_results', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['summary']}</th><td>{record.get('summary', tr['status']['not_available'])}</td></tr>
            <tr><th>{tr['fields']['last_processed']}</th><td>{record.get('last_processed', tr['status']['not_available'])}</td></tr>
            <tr>
                <th>{tr['fields']['raw_text']}</th>
                <td><div class="raw-text">{record.get('text', tr['status']['not_available'])}</div></td>
            </tr>
        </table>
    </div>
</body>
</html>"""
    
    os.makedirs(os.path.dirname(detail_path), exist_ok=True)
    with open(detail_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return os.path.join('html', 'details', filename)

def create_html_page(records, output_path, overall_summary=None, pdf_filename=None):
    """Create main HTML page with links to detail pages.
    
    Args:
        records: List of record dictionaries
        output_path: Path to save the HTML file
        overall_summary: Optional dictionary containing overall patient summary
        pdf_filename: Optional filename of the compiled PDF file
    """
    if not records:
        logging.warning("No records to create HTML page")
        return

    # Ensure records is a list of dictionaries
    if isinstance(records, pd.DataFrame):
        records = records.to_dict('records')

    # Sort records by filename (newest first)
    sorted_records = sorted(records, key=lambda x: x.get('new_filename', ''), reverse=True)
    
    # Load configuration to get language
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logging.info(f"Loaded config: {config}")
    logging.info(f"Output language from config: {config.get('output_language', 'en')}")
    
    output_short_summary_pdf = config.get('output_short_summary_pdf', 'overall_short_summary.pdf')
    
    # Initialize translation manager with configured language
    translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
    translator = TranslationManager(translations_dir, default_language='en')
    translator.set_language(config.get('output_language', 'en'))
    
    # Get translations for static text
    tr = translator.get_all_translations()
    logging.info(f"Current language after setting: {translator.current_language}")
    logging.info(f"Available translations: {list(tr.keys())}")
    
    # Try to generate PDF
    pdf_status = {'available': False, 'error': None}
    if pdf_filename:
        try:
            from pdf_generator import generate_medical_records_pdf
            pdf_path = os.path.join(os.path.dirname(output_path), pdf_filename)
            generate_medical_records_pdf(config_path, pdf_path)
            pdf_status = {'available': True, 'error': None}
        except Exception as e:
            logging.error(f"Error generating PDF: {str(e)}")
            pdf_status = {'available': False, 'error': str(e)}
    
    # Get the absolute path of the output directory
    output_dir = os.path.dirname(os.path.abspath(output_path))
    
    # Filter out the short summary record from the left panel and sort in reverse chronological order
    # The short summary record is identified by visit_type == 'Overall Summary'
    filtered_records = sorted(
        [r for r in sorted_records if r.get('visit_type', '') != 'Overall Summary'],
        key=lambda x: x.get('treatment_date', ''),
        reverse=True
    )
    
    html_content = f"""<!DOCTYPE html>
<html lang="{tr['language_metadata']['code']}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{tr['page_title']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        
        header {{
            background: #fff;
            padding: 1rem;
            border-bottom: 1px solid #ddd;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            flex-shrink: 0;
        }}
        
        .header-main {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        
        .header-info {{
            background: #f8f9fa;
            padding: 0.75rem;
            border-radius: 4px;
            font-size: 0.9rem;
            color: #495057;
            border: 1px solid #dee2e6;
        }}
        
        .header-info code {{
            background: #fff;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Consolas', monospace;
            border: 1px solid #e9ecef;
        }}
        
        .logo {{
            height: 40px;
            width: auto;
        }}
        
        h1 {{
            color: #2c3e50;
            font-size: 1.5rem;
            margin: 0;
        }}
        
        .content {{
            display: flex;
            flex: 1;
            min-height: 0;  /* Important for nested flexbox scrolling */
        }}
        
        .file-list {{
            width: 33%;
            background: #fff;
            border-right: 1px solid #ddd;
            display: flex;
            flex-direction: column;
            min-width: 300px;
        }}
        
        .file-list-header {{
            padding: 1rem;
            background: #f8f9fa;
            border-bottom: 1px solid #ddd;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .file-list-content {{
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
        }}
        
        .file-list ul {{
            list-style: none;
        }}
        
        .file-list li {{
            padding: 0.75rem 1rem;
            cursor: pointer;
            border-radius: 4px;
            margin-bottom: 0.25rem;
            border-left: 3px solid transparent;
            display: flex;
            align-items: center;
            transition: all 0.2s ease;
        }}
        
        .file-list li .number {{
            color: #666;
            font-size: 0.9em;
            margin-right: 1rem;
            min-width: 2em;
            text-align: right;
        }}
        
        .file-list li:hover {{
            background: #f5f6fa;
        }}
        
        .file-list li.active {{
            background: #e3f2fd;
            border-left-color: #3498db;
            font-weight: 600;
        }}
        
        .detail-view {{
            width: 67%;
            background: #f5f6fa;
            display: flex;
            flex-direction: column;
            min-width: 0;  /* Important for text truncation */
        }}
        
        .detail-view-content {{
            flex: 1;
            overflow-y: auto;
            padding: 2rem;
        }}
        
        .record-details {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .overall-summary {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        
        .summary-section {{
            margin-top: 1.5rem;
        }}
        
        .summary-section h3 {{
            color: #2c3e50;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        
        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            width: 200px;
            background: #f8f9fa;
            font-weight: 600;
        }}
        
        .actions {{
            margin-bottom: 1rem;
            text-align: right;
        }}
        
        .btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            color: #333;
            text-decoration: none;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .btn:hover {{
            background: #f8f9fa;
            border-color: #ccc;
        }}
        
        .btn-print svg {{
            margin-right: 0.25rem;
        }}
        
        @media print {{
            body {{
                overflow: visible;
                display: block;
            }}
            
            .file-list, .actions {{
                display: none;
            }}
            
            .detail-view {{
                width: 100%;
                overflow: visible;
            }}
            
            .detail-view-content {{
                overflow: visible;
            }}
        }}
        
        .pdf-button {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 1000;
            padding: 0.5rem 1rem;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            transition: background-color 0.2s;
        }}
        .pdf-button:hover {{
            background-color: #45a049;
        }}
        .pdf-button.error {{
            background-color: #f44336;
        }}
        .pdf-button.error:hover {{
            background-color: #da190b;
        }}
        .pdf-error {{
            display: none;
            position: fixed;
            top: 4rem;
            right: 1rem;
            background-color: #f44336;
            color: white;
            padding: 1rem;
            border-radius: 4px;
            max-width: 300px;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    {f'''
    <button onclick="handlePdfClick()" class="pdf-button {'error' if pdf_status['error'] else ''}" title="{pdf_status['error'] if pdf_status['error'] else tr['actions']['view_complete_pdf']}">
        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
            <path d="M5.523 12.424c.14-.082.293-.162.459-.238a7.878 7.878 0 0 1-.45.606c-.28.337-.498.516-.635.572a.266.266 0 0 1-.035.012.282.282 0 0 1-.026-.044c-.056-.11-.054-.216.04-.36.106-.165.319-.354.647-.548zm2.455-1.647c-.119.025-.237.05-.356.078a21.148 21.148 0 0 0 .5-1.05 12.045 12.045 0 0 0 .51.858c-.217.032-.436.07-.654.114zm2.525.939a3.881 3.881 0 0 1-.435-.41c.228.005.434.022.612.054.317.057.466.147.518.209a.095.095 0 0 1 .026.064.436.436 0 0 1-.06.2.307.307 0 0 1-.094.124.107.107 0 0 1-.069.015c-.09-.003-.258-.066-.498-.256zM8.278 6.97c-.04.244-.108.524-.2.829a4.86 4.86 0 0 1-.089-.346c-.076-.353-.087-.63-.046-.822.038-.177.11-.248.196-.283a.517.517 0 0 1 .145-.04c.013.03.028.092.032.198.005.122-.007.277-.038.465z"/>
            <path fill-rule="evenodd" d="M4 0h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2zm0 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H4z"/>
        </svg>
        {tr['actions']['view_complete_pdf']}
    </button>
    <div id="pdfError" class="pdf-error"></div>
    ''' if pdf_filename else ''}
    <header>
        <div class="header-main">
            <img src="html/Logo.png" alt="Logo" class="logo">
            <h1>{tr['page_title']}</h1>
            {f'<a href="records/{pdf_filename}" target="_blank" class="btn">{tr["actions"]["view_complete_pdf"]}</a>' if pdf_filename else ''}
        </div>
    </header>
    <div class="content">
        <div class="file-list">
            <div class="file-list-header">
                {tr['pdf']['records_included']} ({len(filtered_records)})
            </div>
            <div class="file-list-content">
                <ul>
                    <li class="file-item" data-index="-1">
                        <span class="number">1.</span>
                        {tr['pdf']['overall_summary']}
                    </li>
                    {''.join([
                        f'<li class="file-item" data-index="{i}">'
                        f'<span class="number">{i + 2}.</span>'
                        f'{record.get("new_filename", "Unnamed Record")}'
                        f'</li>'
                        for i, record in enumerate(filtered_records)
                    ])}
                </ul>
            </div>
        </div>
        <div class="detail-view">
            <div class="detail-view-content">
                <div class="record-details">
                    <p>Select a record from the list to view details.</p>
                </div>
            </div>
        </div>
    </div>
    <script>
        // Initialize records data (including overall summary and short summary PDF name)
        const records = {json.dumps(filtered_records)};
        const overallSummary = {json.dumps(overall_summary) if overall_summary else 'null'};
        const translations = {json.dumps(tr)};
        const pdfStatus = {json.dumps(pdf_status)};
        const shortSummaryPdf = "{output_short_summary_pdf}";
        let currentIndex = -1;
        
        // Format lists for display
        function formatList(items) {{
            if (!items) return translations.status.not_available;
            if (typeof items === 'string') return items;
            if (Array.isArray(items)) return items.join(', ') || translations.status.not_available;
            return translations.status.not_available;
        }}
        
        // Helper function to format array sections
        const formatArraySection = (array, listType = '') => {{
            if (!array || !Array.isArray(array)) return translations.status.not_available;
            if (listType === 'bullet') {{
                return '<ul>' + array.map(item => '<li>' + item + '</li>').join('') + '</ul>';
            }}
            return array.map(item => '<p>' + item + '</p>').join('');
        }};
        
        // Show record details
        function showRecord(index) {{
            // Update active state in file list
            document.querySelectorAll('.file-item').forEach(item => item.classList.remove('active'));
            const activeItem = document.querySelector(`[data-index="${{index}}"]`);
            if (activeItem) {{
                activeItem.classList.add('active');
            }}
            
            if (index === -1) {{
                // Show overall summary
                const summaryHtml = '<div class="record-details">' +
                    '<div class="actions">' +
                        '<button class="btn btn-print" onclick="window.print()">' +
                            '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">' +
                                '<path d="M2.5 8a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>' +
                                '<path d="M5 1a2 2 0 0 0-2 2v2H2a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h1v1a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-1h1a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-1V3a2 2 0 0 0-2-2H5zM4 3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2H4V3zm1 5a2 2 0 0 0-2 2v1H2a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v-1a2 2 0 0 0-2-2H5zm7 2v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1z"/>' +
                            '</svg>' +
                            translations.actions.print +
                        '</button>' +
                        '<a href="' + shortSummaryPdf + '" target="_blank" class="btn">' + translations.actions.view_original + '</a>' +
                    '</div>' +
                    '<h2>' + translations.pdf.overall_summary + '</h2>' +
                    '<div class="summary-section">' +
                        '<h3>' + translations.summary_sections.patient_description + '</h3>' +
                        '<p>' + (overallSummary?.patient?.section || translations.status.not_available) + '</p>' +
                    '</div>' +
                    '<div class="summary-section">' +
                        '<h3>' + translations.summary_sections.medical_history + '</h3>' +
                        formatArraySection(overallSummary?.medical_history?.section, 'bullet') +
                    '</div>' +
                    '<div class="summary-section">' +
                        '<h3>' + translations.summary_sections.summary + '</h3>' +
                        formatArraySection(overallSummary?.summary?.section) +
                    '</div>' +
                    '<div class="summary-section">' +
                        '<h3>' + translations.summary_sections.key_findings + '</h3>' +
                        formatArraySection(overallSummary?.key_findings?.section, 'bullet') +
                    '</div>' +
                    '<div class="summary-section">' +
                        '<h3>' + translations.summary_sections.recommendations + '</h3>' +
                        formatArraySection(overallSummary?.recommendations?.section, 'bullet') +
                    '</div>' +
                '</div>';
                document.querySelector('.record-details').innerHTML = summaryHtml;
                currentIndex = -1;
            }} else if (index >= 0 && index < records.length) {{
                currentIndex = index;
                const record = records[index];
                
                // Update record details
                const detailsHtml = 
                    '<div class="actions">' +
                        '<button class="btn btn-print" onclick="window.print()">' +
                            '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">' +
                                '<path d="M2.5 8a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>' +
                                '<path d="M5 1a2 2 0 0 0-2 2v2H2a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h1v1a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-1h1a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-1V3a2 2 0 0 0-2-2H5zM4 3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2H4V3zm1 5a2 2 0 0 0-2 2v1H2a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v-1a2 2 0 0 0-2-2H5zm7 2v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1z"/>' +
                            '</svg>' +
                            translations.actions.print +
                        '</button>' +
                        '<a href="records/' + record.new_filename + '" target="_blank" class="btn">' + translations.actions.view_original + '</a>' +
                    '</div>' +
                    '<table>' +
                        '<tr><th>' + translations.fields.treatment_date_regex + '</th><td>' + (record.treatment_date || translations.status.not_available) + '</td></tr>' +
                        '<tr><th>' + translations.fields.treatment_date_ai + '</th><td>' + (record.ai_treatment_date || translations.status.not_available) + '</td></tr>' +
                        '<tr><th>' + translations.fields.visit_type + '</th><td>' + (record.visit_type || translations.status.not_available) + '</td></tr>' +
                        '<tr><th>' + translations.fields.provider_name + '</th><td>' + (record.provider_name || translations.status.not_available) + '</td></tr>' +
                        '<tr><th>' + translations.fields.provider_facility + '</th><td>' + (record.provider_facility || translations.status.not_available) + '</td></tr>' +
                        '<tr><th>' + translations.fields.primary_condition + '</th><td>' + (record.primary_condition || translations.status.not_available) + '</td></tr>' +
                        '<tr><th>' + translations.fields.diagnoses + '</th><td>' + formatList(record.diagnoses) + '</td></tr>' +
                        '<tr><th>' + translations.fields.treatments + '</th><td>' + formatList(record.treatments) + '</td></tr>' +
                        '<tr><th>' + translations.fields.medications + '</th><td>' + formatList(record.medications) + '</td></tr>' +
                        '<tr><th>' + translations.fields.test_results + '</th><td>' + formatList(record.test_results) + '</td></tr>' +
                        '<tr><th>' + translations.fields.summary + '</th><td>' + (record.summary || translations.status.not_available) + '</td></tr>' +
                        '<tr><th>' + translations.fields.last_processed + '</th><td>' + (record.last_processed || translations.status.not_available) + '</td></tr>' +
                    '</table>';
                
                document.querySelector('.record-details').innerHTML = detailsHtml;
            }}
        }}
        
        // Navigation functions
        function navigateUp() {{
            if (currentIndex > -1) {{
                showRecord(currentIndex - 1);
            }}
        }}
        
        function navigateDown() {{
            if (currentIndex < records.length - 1) {{
                showRecord(currentIndex + 1);
            }}
        }}
        
        // Event listeners
        document.addEventListener('DOMContentLoaded', function() {{
            // Add click listeners to file items
            document.querySelectorAll('.file-item').forEach(item => {{
                item.addEventListener('click', function() {{
                    const index = parseInt(this.getAttribute('data-index'));
                    showRecord(index);
                }});
            }});
            
            // Keyboard navigation
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'ArrowUp') {{
                    e.preventDefault();
                    navigateUp();
                }} else if (e.key === 'ArrowDown') {{
                    e.preventDefault();
                    navigateDown();
                }}
            }});
            
            // Show first record by default
            showRecord(-1);
        }});
        
        function handlePdfClick() {{
            if (pdfStatus.available) {{
                window.open('{pdf_filename}', '_blank');
            }} else if (pdfStatus.error) {{
                const errorDiv = document.getElementById('pdfError');
                errorDiv.textContent = pdfStatus.error;
                errorDiv.style.display = 'block';
                setTimeout(() => {{
                    errorDiv.style.display = 'none';
                }}, 5000);
            }}
        }}
    </script>
</body>
</html>"""

    # Write the HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Create detail pages directory
    details_dir = os.path.join(output_dir, 'html', 'details')
    os.makedirs(details_dir, exist_ok=True)
    
    # Create individual detail pages (for filtered records only, since summary has no detail page)
    for record in filtered_records:
        create_detail_page(record, output_dir)

def save_to_csv(records, csv_path):
    """Save extracted data and metadata to CSV file."""
    df = pd.DataFrame([{
        'File Path': r['file_path'],
        'Original Filename': r['original_filename'],
        'New Filename': r['new_filename'],
        'Checksum': r['checksum'],
        'Summary': r.get('summary', 'No summary available'),
        'Text': r['text'],
        'API Response': r.get('api_response', {})
    } for r in records])
    
    df.to_csv(csv_path, index=False)
    logging.info(f"Saved extracted data to CSV: {csv_path}")
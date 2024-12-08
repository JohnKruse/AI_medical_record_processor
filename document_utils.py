import pandas as pd
import logging
import os
import json
import shutil

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
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Record Details - {record['new_filename']}</title>
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
        <h2 class="record-title">{{record['new_filename']}}</h2>
        <div class="actions">
            <button class="btn btn-print" onclick="window.print()">
                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M2.5 8a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
                    <path d="M5 1a2 2 0 0 0-2 2v2H2a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h1v1a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-1h1a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-1V3a2 2 0 0 0-2-2H5zM4 3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2H4V3zm1 5a2 2 0 0 0-2 2v1H2a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v-1a2 2 0 0 0-2-2H5zm7 2v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1z"/>
                </svg>
                Print
            </button>
            <a href="../../records/{{record['new_filename']}}" target="_blank" class="btn">View Original</a>
        </div>
        <table>
            <tr><th>Treatment Date (Regex)</th><td>{{record.get('treatment_date', 'N/A')}}</td></tr>
            <tr><th>Treatment Date (AI)</th><td>{{record.get('ai_treatment_date', 'N/A')}}</td></tr>
            <tr><th>Visit Type</th><td>{{record.get('visit_type', 'N/A')}}</td></tr>
            <tr><th>Provider Name</th><td>{{record.get('provider_name', 'N/A')}}</td></tr>
            <tr><th>Provider Facility</th><td>{{record.get('provider_facility', 'N/A')}}</td></tr>
            <tr><th>Primary Condition</th><td>{{record.get('primary_condition', 'N/A')}}</td></tr>
            <tr><th>Diagnoses</th><td>{{record.get('diagnoses', 'N/A')}}</td></tr>
            <tr><th>Treatments</th><td>{{record.get('treatments', 'N/A')}}</td></tr>
            <tr><th>Medications</th><td>{{record.get('medications', 'N/A')}}</td></tr>
            <tr><th>Test Results</th><td>{{record.get('test_results', 'N/A')}}</td></tr>
            <tr><th>Summary</th><td>{{record.get('summary', 'N/A')}}</td></tr>
            <tr><th>Last Processed</th><td>{{record.get('last_processed', 'N/A')}}</td></tr>
            <tr>
                <th>Raw Extracted Text</th>
                <td><div class="raw-text">{{record.get('text', 'N/A')}}</div></td>
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
    
    # Get the absolute path of the output directory
    output_dir = os.path.dirname(os.path.abspath(output_path))
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Records Viewer</title>
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
        
        .btn-pdf {{
            background-color: #4CAF50;
            color: white;
            border: none;
            margin-left: auto;
        }}
        
        .btn-pdf:hover {{
            background-color: #45a049;
            color: white;
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-main">
            <img src="html/Logo.png" alt="Logo" class="logo">
            <h1>Medical Records Viewer</h1>
            {f'<a href="records/{pdf_filename}" target="_blank" class="btn btn-pdf">View Complete Medical Records PDF</a>' if pdf_filename else ''}
        </div>
    </header>
    <div class="content">
        <div class="file-list">
            <div class="file-list-header">
                Records ({len(sorted_records)})
            </div>
            <div class="file-list-content">
                <ul>
                    <li class="file-item" data-index="-1">
                        <span class="number">1.</span>
                        Overall Summary
                    </li>
                    {''.join([
                        f'<li class="file-item" data-index="{i}">'
                        f'<span class="number">{i + 2}.</span>'
                        f'{record.get("new_filename", "Unnamed Record")}'
                        f'</li>'
                        for i, record in enumerate(sorted_records)
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
        // Initialize records data
        const records = {json.dumps(sorted_records)};
        const overallSummary = {json.dumps(overall_summary) if overall_summary else 'null'};
        let currentIndex = -1;
        
        // Format lists for display
        function formatList(items) {{
            if (!items) return 'N/A';
            if (typeof items === 'string') return items;
            if (Array.isArray(items)) return items.join(', ') || 'N/A';
            return 'N/A';
        }}
        
        // Helper function to format array sections
        const formatArraySection = (array, listType = '') => {{
            if (!array || !Array.isArray(array)) return 'No information available';
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
                    '<h2>Overall Summary</h2>' +
                    '<div class="summary-section">' +
                        '<h3>Patient Description</h3>' +
                        '<p>' + (overallSummary?.patient?.section || 'No patient description available') + '</p>' +
                    '</div>' +
                    '<div class="summary-section">' +
                        '<h3>Medical History</h3>' +
                        formatArraySection(overallSummary?.medical_history?.section, 'bullet') +
                    '</div>' +
                    '<div class="summary-section">' +
                        '<h3>Summary</h3>' +
                        formatArraySection(overallSummary?.summary?.section) +
                    '</div>' +
                    '<div class="summary-section">' +
                        '<h3>Key Findings</h3>' +
                        formatArraySection(overallSummary?.key_findings?.section, 'bullet') +
                    '</div>' +
                    '<div class="summary-section">' +
                        '<h3>Recommendations</h3>' +
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
                            'Print' +
                        '</button>' +
                        '<a href="records/' + record.new_filename + '" target="_blank" class="btn">View Original</a>' +
                    '</div>' +
                    '<table>' +
                        '<tr><th>Treatment Date (Regex)</th><td>' + (record.treatment_date || 'N/A') + '</td></tr>' +
                        '<tr><th>Treatment Date (AI)</th><td>' + (record.ai_treatment_date || 'N/A') + '</td></tr>' +
                        '<tr><th>Visit Type</th><td>' + (record.visit_type || 'N/A') + '</td></tr>' +
                        '<tr><th>Provider Name</th><td>' + (record.provider_name || 'N/A') + '</td></tr>' +
                        '<tr><th>Provider Facility</th><td>' + (record.provider_facility || 'N/A') + '</td></tr>' +
                        '<tr><th>Primary Condition</th><td>' + (record.primary_condition || 'N/A') + '</td></tr>' +
                        '<tr><th>Diagnoses</th><td>' + formatList(record.diagnoses) + '</td></tr>' +
                        '<tr><th>Treatments</th><td>' + formatList(record.treatments) + '</td></tr>' +
                        '<tr><th>Medications</th><td>' + formatList(record.medications) + '</td></tr>' +
                        '<tr><th>Test Results</th><td>' + formatList(record.test_results) + '</td></tr>' +
                        '<tr><th>Summary</th><td>' + (record.summary || 'N/A') + '</td></tr>' +
                        '<tr><th>Last Processed</th><td>' + (record.last_processed || 'N/A') + '</td></tr>' +
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
    </script>
</body>
</html>"""
    
    # Write the HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Create detail pages directory
    details_dir = os.path.join(output_dir, 'html', 'details')
    os.makedirs(details_dir, exist_ok=True)
    
    # Create individual detail pages
    for record in sorted_records:
        create_detail_page(record, output_dir)

def save_to_csv(records, csv_path):
    """Save extracted data and metadata to CSV file."""
    df = pd.DataFrame([{
        'File Path': r['file_path'],
        'Original Filename': r['original_filename'],
        'New Filename': r['new_filename'],
        'Checksum': r['checksum'],
        'Summary': r.get('summary', 'No summary available'),  # Use .get() to avoid KeyError
        'Text': r['text'],
        'API Response': r.get('api_response', {})  # Add the API response column
    } for r in records])
    
    df.to_csv(csv_path, index=False)
    logging.info(f"Saved extracted data to CSV: {csv_path}")

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
                Print
            </button>
            <a href="../../records/{record['new_filename']}" target="_blank" class="btn">View Original</a>
        </div>
        <table>
            <tr><th>Treatment Date (Regex)</th><td>{record.get('treatment_date', 'N/A')}</td></tr>
            <tr><th>Treatment Date (AI)</th><td>{record.get('ai_treatment_date', 'N/A')}</td></tr>
            <tr><th>Visit Type</th><td>{record.get('visit_type', 'N/A')}</td></tr>
            <tr><th>Provider Name</th><td>{record.get('provider_name', 'N/A')}</td></tr>
            <tr><th>Provider Facility</th><td>{record.get('provider_facility', 'N/A')}</td></tr>
            <tr><th>Primary Condition</th><td>{record.get('primary_condition', 'N/A')}</td></tr>
            <tr><th>Diagnoses</th><td>{record.get('diagnoses', 'N/A')}</td></tr>
            <tr><th>Treatments</th><td>{record.get('treatments', 'N/A')}</td></tr>
            <tr><th>Medications</th><td>{record.get('medications', 'N/A')}</td></tr>
            <tr><th>Test Results</th><td>{record.get('test_results', 'N/A')}</td></tr>
            <tr><th>Summary</th><td>{record.get('summary', 'N/A')}</td></tr>
            <tr><th>Last Processed</th><td>{record.get('last_processed', 'N/A')}</td></tr>
        </table>
    </div>
</body>
</html>"""
    
    os.makedirs(os.path.dirname(detail_path), exist_ok=True)
    with open(detail_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return os.path.join('html', 'details', filename)

def create_html_page(records, output_path):
    """Create main HTML page with links to detail pages."""
    # Sort records by filename in reverse order
    sorted_records = sorted(records, key=lambda x: x.get('new_filename', ''), reverse=True)
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Records Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        header {
            background: #fff;
            padding: 1rem;
            border-bottom: 1px solid #ddd;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .logo {
            height: 40px;
            width: auto;
        }
        
        h1 {
            color: #2c3e50;
            font-size: 1.5rem;
        }
        
        .content {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        
        .file-list {
            width: 33%;
            background: #fff;
            border-right: 1px solid #ddd;
            overflow-y: auto;
            padding: 1rem;
        }
        
        .file-list ul {
            list-style: none;
        }
        
        .file-list li {
            padding: 0.75rem 1rem;
            cursor: pointer;
            border-radius: 4px;
            margin-bottom: 0.25rem;
            border-left: 3px solid transparent;
            display: flex;
            align-items: center;
        }
        
        .file-list li .number {
            color: #666;
            font-size: 0.9em;
            margin-right: 1rem;
            min-width: 2em;
            text-align: right;
        }
        
        .file-list li:hover {
            background: #f5f6fa;
        }
        
        .file-list li.active {
            background: #e3f2fd;
            border-left-color: #3498db;
            font-weight: 600;
        }
        
        .detail-view {
            width: 67%;
            overflow-y: auto;
            padding: 2rem;
            background: #f5f6fa;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        
        th, td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            width: 200px;
            background: #f8f9fa;
            font-weight: 600;
        }
        
        .actions {
            margin-bottom: 1rem;
            text-align: right;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            font-size: 0.9rem;
        }
        
        .btn:hover {
            opacity: 0.9;
        }
        
        .record-title {
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: #2c3e50;
        }
    </style>
</head>
<body>
    <header>
        <img src="html/Logo.png" alt="Medical Records" class="logo">
        <h1>Medical Records Viewer</h1>
    </header>
    
    <div class="content">
        <div class="file-list">
            <ul>"""
    
    # Add file list items with numbers
    for i, record in enumerate(sorted_records, 1):
        filename = record.get('new_filename', os.path.basename(record['file_path']))
        html_content += f'\n                <li data-index="{i-1}"><span class="number">#{i}</span>{filename}</li>'

    html_content += """
            </ul>
        </div>
        <div class="detail-view">
            <div id="record-details"></div>
        </div>
    </div>

    <script>
        const records = """ + json.dumps(sorted_records, indent=2) + """;
        let currentIndex = -1;
        
        function showRecord(index) {
            if (index < 0 || index >= records.length) return;
            currentIndex = index;
            
            const record = records[index];
            const detailsHtml = `
                <h2 class="record-title">${record.new_filename}</h2>
                <div class="actions">
                    <button class="btn" onclick="window.print()">
                        <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M2.5 8a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
                            <path d="M5 1a2 2 0 0 0-2 2v2H2a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h1v1a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-1h1a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-1V3a2 2 0 0 0-2-2H5zM4 3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2H4V3zm1 5a2 2 0 0 0-2 2v1H2a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v-1a2 2 0 0 0-2-2H5zm7 2v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1z"/>
                        </svg>
                        Print
                    </button>
                    <a href="records/${record.new_filename}" target="_blank" class="btn">View Original</a>
                </div>
                <table>
                    <tr><th>Treatment Date (Regex)</th><td>${record.treatment_date || 'N/A'}</td></tr>
                    <tr><th>Treatment Date (AI)</th><td>${record.ai_treatment_date || 'N/A'}</td></tr>
                    <tr><th>Visit Type</th><td>${record.visit_type || 'N/A'}</td></tr>
                    <tr><th>Provider Name</th><td>${record.provider_name || 'N/A'}</td></tr>
                    <tr><th>Provider Facility</th><td>${record.provider_facility || 'N/A'}</td></tr>
                    <tr><th>Primary Condition</th><td>${record.primary_condition || 'N/A'}</td></tr>
                    <tr><th>Diagnoses</th><td>${record.diagnoses || 'N/A'}</td></tr>
                    <tr><th>Treatments</th><td>${record.treatments || 'N/A'}</td></tr>
                    <tr><th>Medications</th><td>${record.medications || 'N/A'}</td></tr>
                    <tr><th>Test Results</th><td>${record.test_results || 'N/A'}</td></tr>
                    <tr><th>Summary</th><td>${record.summary || 'N/A'}</td></tr>
                    <tr><th>Last Processed</th><td>${record.last_processed || 'N/A'}</td></tr>
                </table>
            `;
            
            document.getElementById('record-details').innerHTML = detailsHtml;
            
            // Update active state
            document.querySelectorAll('.file-list li').forEach(item => item.classList.remove('active'));
            document.querySelector(`[data-index="${index}"]`).classList.add('active');
        }
        
        // Add click handlers
        document.querySelectorAll('.file-list li').forEach((item, index) => {
            item.addEventListener('click', () => showRecord(index));
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowUp' && currentIndex > 0) {
                e.preventDefault();
                showRecord(currentIndex - 1);
            } else if (e.key === 'ArrowDown' && currentIndex < records.length - 1) {
                e.preventDefault();
                showRecord(currentIndex + 1);
            }
        });
        
        // Show first record
        if (records.length > 0) showRecord(0);
    </script>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(html_content)
    logging.info(f"Created HTML summary page: {output_path}")

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

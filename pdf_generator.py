import os
import json
import yaml
import pandas as pd
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus.tables import Table, TableStyle
import PyPDF2
import tempfile

def generate_medical_records_pdf(config_path, output_pdf):
    """Generate a PDF report of medical records."""
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f) if config_path.endswith('.json') else yaml.safe_load(f)
    
    # Setup paths
    output_location = config['output_location']
    data_file = os.path.join(output_location, 'data_files', 'extracted_data.csv')
    records_dir = os.path.join(output_location, 'records')
    
    # Load records
    df = pd.read_csv(data_file)
    
    # Sort records by treatment date
    df['treatment_date'] = pd.to_datetime(df['treatment_date'], errors='coerce')
    df = df.sort_values('treatment_date', ascending=False)
    
    # Create a temporary PDF for the cover pages and TOC
    temp_cover_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
    
    # Create PDF document with larger margins
    doc = SimpleDocTemplate(
        temp_cover_pdf,
        pagesize=letter,
        rightMargin=1*inch,
        leftMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20
    )
    normal_style = styles['Normal']
    
    # Build PDF content
    story = []
    
    # 1. Cover sheet
    patient_name = df['patient_last_name'].iloc[0] if not pd.isna(df['patient_last_name'].iloc[0]) else "Unknown"
    patient_fname = df['patient_first_name'].iloc[0] if not pd.isna(df['patient_first_name'].iloc[0]) else ""
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    story.append(Paragraph(f"Medical Records<br/>{patient_name}, {patient_fname}", title_style))
    story.append(Paragraph(current_date, title_style))
    story.append(PageBreak())
    
    # 2. Overall Summary page
    if os.path.exists(os.path.join(output_location, 'data_files', 'overall_summary.txt')):
        with open(os.path.join(output_location, 'data_files', 'overall_summary.txt'), 'r') as f:
            summary = f.read()
        story.append(Paragraph("Overall Summary", heading_style))
        story.append(Paragraph(summary, normal_style))
        story.append(PageBreak())
    
    # 3. Records Included
    story.append(Paragraph("Records Included", heading_style))
    
    # Create table of contents with proper column widths
    records_data = []
    for i, (_, record) in enumerate(df.iterrows(), 1):
        records_data.append([
            str(i),
            record['treatment_date'].strftime('%Y-%m-%d') if pd.notna(record['treatment_date']) else 'Unknown',
            str(record['visit_type']) if pd.notna(record['visit_type']) else 'Unknown',
            str(record['provider_name']) if pd.notna(record['provider_name']) else 'Unknown',
            str(record['provider_facility']) if pd.notna(record['provider_facility']) else 'Unknown'
        ])
    
    # Table headers
    headers = ['#', 'Treatment Date', 'Visit Type', 'Doctor Name', 'Provider Facility']
    col_widths = [0.3*inch, 1.2*inch, 1.5*inch, 1.5*inch, 2*inch]  # Adjusted column widths
    records_table = Table([headers] + records_data, colWidths=col_widths)
    records_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(records_table)
    story.append(PageBreak())
    
    # Build the cover pages PDF
    doc.build(story)
    
    # Now merge all PDFs
    pdf_merger = PyPDF2.PdfMerger()
    
    # Add cover pages
    pdf_merger.append(temp_cover_pdf)
    
    # Add each record's PDF with its cover page
    for i, (_, record) in enumerate(df.iterrows(), 1):
        # Create a temporary PDF for the record cover page
        temp_record_cover = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        doc = SimpleDocTemplate(
            temp_record_cover,
            pagesize=letter,
            rightMargin=1*inch,
            leftMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        story = []
        story.append(Paragraph(f"Record {i}", heading_style))
        
        record_info = [
            ('Treatment Date', record['treatment_date'].strftime('%Y-%m-%d') if pd.notna(record['treatment_date']) else 'Unknown'),
            ('Visit Type', str(record['visit_type']) if pd.notna(record['visit_type']) else 'Unknown'),
            ('Doctor Name', str(record['provider_name']) if pd.notna(record['provider_name']) else 'Unknown'),
            ('Provider Facility', str(record['provider_facility']) if pd.notna(record['provider_facility']) else 'Unknown'),
            ('Primary Condition', str(record['primary_condition']) if pd.notna(record['primary_condition']) else 'Unknown'),
            ('Diagnosis', str(record['diagnoses']) if pd.notna(record['diagnoses']) else 'Unknown')
        ]
        
        for label, value in record_info:
            story.append(Paragraph(f"<b>{label}:</b> {value}", normal_style))
            story.append(Spacer(1, 12))
        
        doc.build(story)
        
        # Add record cover page
        pdf_merger.append(temp_record_cover)
        
        # Add the actual record PDF if it exists
        record_pdf = os.path.join(records_dir, record['new_filename'])
        if os.path.exists(record_pdf):
            pdf_merger.append(record_pdf)
        
        # Clean up temporary cover page
        os.unlink(temp_record_cover)
    
    # Write the final merged PDF
    output_path = os.path.join(output_location, output_pdf)
    with open(output_path, 'wb') as output_file:
        pdf_merger.write(output_file)
    
    # Clean up
    pdf_merger.close()
    os.unlink(temp_cover_pdf)

if __name__ == "__main__":
    config_path = "config/config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    generate_medical_records_pdf(config_path, config['output_pdf'])

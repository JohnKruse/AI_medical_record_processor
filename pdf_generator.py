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
from translation_manager import TranslationManager
import logging

def generate_medical_records_pdf(config_path, output_pdf):
    """Generate a PDF report of medical records."""
    try:
        # Load configuration
        with open(config_path, 'r') as f:
            config = json.load(f) if config_path.endswith('.json') else yaml.safe_load(f)
        
        # Initialize translation manager
        translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
        translator = TranslationManager(translations_dir, default_language='en')
        translator.set_language(config.get('output_language', 'en'))
        
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
        patient_name = df['patient_last_name'].iloc[0] if not pd.isna(df['patient_last_name'].iloc[0]) else translator.get('status.unknown')
        patient_fname = df['patient_first_name'].iloc[0] if not pd.isna(df['patient_first_name'].iloc[0]) else ""
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        story.append(Paragraph(f"{translator.get('pdf.medical_records')}<br/>{patient_name}, {patient_fname}", title_style))
        story.append(Paragraph(current_date, title_style))
        story.append(PageBreak())
        
        # 2. Overall Summary page
        if os.path.exists(os.path.join(output_location, 'data_files', 'overall_summary.txt')):
            with open(os.path.join(output_location, 'data_files', 'overall_summary.txt'), 'r') as f:
                summary = f.read()
            story.append(Paragraph(translator.get('pdf.overall_summary'), heading_style))
            story.append(Paragraph(summary, normal_style))
            story.append(PageBreak())
        
        # 3. Records Included
        story.append(Paragraph(translator.get('pdf.records_included'), heading_style))
        
        # Create table of contents with proper column widths
        records_data = []
        for i, (_, record) in enumerate(df.iterrows(), 1):
            records_data.append([
                str(i),
                record['treatment_date'].strftime('%Y-%m-%d') if pd.notna(record['treatment_date']) else translator.get('status.unknown'),
                Paragraph(str(record['visit_type']) if pd.notna(record['visit_type']) else translator.get('status.unknown'), normal_style),
                Paragraph(str(record['provider_name']) if pd.notna(record['provider_name']) else translator.get('status.unknown'), normal_style)
            ])
        
        # Table headers
        headers = [
            Paragraph(translator.get('table.number'), normal_style),
            Paragraph(translator.get('fields.treatment_date'), normal_style),
            Paragraph(translator.get('fields.visit_type'), normal_style),
            Paragraph(translator.get('fields.provider_name'), normal_style)
        ]
        
        # Calculate available width (letter page width minus margins)
        available_width = letter[0] - 2*inch  # Total width minus left and right margins
        
        # Distribute column widths proportionally
        col_widths = [
            0.5*inch,              # # column
            1.5*inch,             # Treatment Date
            2.0*inch,             # Visit Type
            available_width - (0.5 + 1.5 + 2.0)*inch  # Doctor Name gets remaining space
        ]
        
        records_table = Table([headers] + records_data, colWidths=col_widths)
        records_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            
            # Grid styling
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.grey),  # Thicker line below header
            
            # Alignment
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Align to top for wrapped text
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            
            # First two columns (# and date) centered
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
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
            story.append(Paragraph(f"{translator.get('pdf.record_number')} {i}", heading_style))
            
            record_info = [
                (translator.get('fields.treatment_date'), 
                 record['treatment_date'].strftime('%Y-%m-%d') if pd.notna(record['treatment_date']) else translator.get('status.unknown')),
                (translator.get('fields.visit_type'), 
                 str(record['visit_type']) if pd.notna(record['visit_type']) else translator.get('status.unknown')),
                (translator.get('fields.provider_name'), 
                 str(record['provider_name']) if pd.notna(record['provider_name']) else translator.get('status.unknown')),
                (translator.get('fields.primary_condition'), 
                 str(record['primary_condition']) if pd.notna(record['primary_condition']) else translator.get('status.unknown')),
                (translator.get('fields.diagnoses'), 
                 str(record['diagnoses']) if pd.notna(record['diagnoses']) else translator.get('status.unknown'))
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
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_overall_summary_pdf(config_path_or_dict, output_pdf=None):
    """Generate a PDF report from the overall summary JSON."""
    try:
        # Handle config input
        if isinstance(config_path_or_dict, dict):
            config = config_path_or_dict
        else:
            with open(config_path_or_dict, 'r') as f:
                config = json.load(f) if str(config_path_or_dict).endswith('.json') else yaml.safe_load(f)
        
        # Initialize translation manager
        translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
        translator = TranslationManager(translations_dir, default_language='en')
        translator.set_language(config.get('output_language', 'en'))
        
        # Setup paths
        output_location = config['output_location']
        summary_file = os.path.join(output_location, 'data_files', 'overall_summary.json')
        
        if not os.path.exists(summary_file):
            raise FileNotFoundError(f"Overall summary file not found: {summary_file}")
            
        # Load summary data
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
            
        # Set output PDF path if not provided
        if output_pdf is None:
            current_date = datetime.now().strftime('%Y%m%d')
            output_pdf = os.path.join(output_location, 'records', f'overall_summary_{current_date}.pdf')
            
        # Create PDF document
        doc = SimpleDocTemplate(
            output_pdf,
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
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            leading=14,
            spaceAfter=12
        )
        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=12,
            leading=14,
            leftIndent=20,
            spaceAfter=12
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("Medical Records Summary", title_style))
        story.append(Paragraph(datetime.now().strftime('%Y-%m-%d'), normal_style))
        story.append(Spacer(1, 30))
        
        # Process each section in the JSON
        for section_name, section_data in summary_data.items():
            # Create section heading by converting section_name to title case
            heading = section_name.replace('_', ' ').title()
            story.append(Paragraph(heading, heading_style))
            
            # Get the section content
            content = section_data.get('section', '')
            
            # Handle different content types
            if isinstance(content, str):
                # Single paragraph
                story.append(Paragraph(content, normal_style))
            elif isinstance(content, list):
                # Handle each list item
                for item in content:
                    if section_name == 'medical_history':
                        # For medical history, each visit is a bullet point with indented details
                        visit_entries = str(item).split('\n\n')  # Split by double newline to separate visits
                        for visit in visit_entries:
                            if visit.strip():
                                # Add bullet point for the visit
                                story.append(Paragraph(f"• {visit.replace('\n', '<br/>')}", bullet_style))
                    else:
                        # For other sections, simple bullet points
                        story.append(Paragraph(f"• {item}", bullet_style))
            
            # Add space after section
            story.append(Spacer(1, 20))
            
            # If there's a summary subsection (specifically for medical_history)
            if isinstance(section_data, dict) and 'summary' in section_data:
                story.append(Paragraph("Summary", heading_style))
                story.append(Paragraph(section_data['summary'], normal_style))
                story.append(Spacer(1, 20))
        
        # Build the PDF
        doc.build(story)
        
        return output_pdf
        
    except Exception as e:
        logging.error(f"Error generating overall summary PDF: {str(e)}")
        raise

if __name__ == "__main__":
    config_path = "config/config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Generate overall summary PDF
    try:
        summary_pdf = generate_overall_summary_pdf(config)
        print(f"Generated overall summary PDF: {summary_pdf}")
    except Exception as e:
        print(f"Error generating overall summary PDF: {str(e)}")
    
    generate_medical_records_pdf(config_path, config['output_pdf'])

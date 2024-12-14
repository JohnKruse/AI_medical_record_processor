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
    """Generate a PDF report of medical records with requested structure:
       - Cover page with "medical_records" title, patient name, date YYYY-MM-DD
       - Table of contents
       - Summary (the short summary PDF specified by output_short_summary_pdf)
       - Each doc: doc cover page (with info) + original file
    """
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
        
        # short summary pdf
        short_summary_pdf = os.path.join(output_location, config.get('output_short_summary_pdf', 'overall_short_summary.pdf'))
        
        # Load records
        df = pd.read_csv(data_file)
        
        # Filter out the "Overall Summary" since it's the short summary PDF we will add separately
        # Actually, we will just handle it by not including it in the TOC as a separate doc. The instructions say the rollup includes it after the TOC.
        df['treatment_date'] = pd.to_datetime(df['treatment_date'], errors='coerce')
        df = df.sort_values('treatment_date', ascending=False)
        
        # Create a temporary PDF for the cover and TOC
        temp_cover_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        
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
        
        # Cover page
        patient_name = df['patient_last_name'].iloc[0] if not pd.isna(df['patient_last_name'].iloc[0]) else translator.get('status.unknown')
        patient_fname = df['patient_first_name'].iloc[0] if not pd.isna(df['patient_first_name'].iloc[0]) else ""
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        story.append(Paragraph(f"{translator.get('pdf.medical_records')}<br/>{patient_name}, {patient_fname}", title_style))
        story.append(Paragraph(current_date, title_style))
        story.append(PageBreak())
        
        # Table of contents
        story.append(Paragraph(translator.get('pdf.records_included'), heading_style))
        
        # Filter out the overall summary record from the TOC listing, since we will add the short summary pdf separately
        doc_records = df[df['visit_type'] != 'Overall Summary'].copy()
        
        records_data = []
        for i, (_, record) in enumerate(doc_records.iterrows(), 1):
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
        
        available_width = letter[0] - 2*inch
        col_widths = [
            0.5*inch,
            1.5*inch,
            2.0*inch,
            available_width - (0.5 + 1.5 + 2.0)*inch
        ]
        
        records_table = Table([headers] + records_data, colWidths=col_widths)
        records_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),
        ]))
        
        story.append(records_table)
        story.append(PageBreak())
        
        # Build the cover + TOC PDF
        doc.build(story)
        
        # Now merge all PDFs
        pdf_merger = PyPDF2.PdfMerger()
        
        # Add cover+TOC
        pdf_merger.append(temp_cover_pdf)
        
        # Add the short summary PDF (overall summary) after TOC
        if os.path.exists(short_summary_pdf):
            pdf_merger.append(short_summary_pdf)
        
        # Add each doc with its cover
        for i, (_, record) in enumerate(doc_records.iterrows(), 1):
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
            
            pdf_merger.append(temp_record_cover)
            
            record_pdf = os.path.join(records_dir, record['new_filename'])
            if os.path.exists(record_pdf):
                pdf_merger.append(record_pdf)
            
            os.unlink(temp_record_cover)
        
        # Write the final merged PDF
        output_path = os.path.join(output_location, output_pdf)
        with open(output_path, 'wb') as output_file:
            pdf_merger.write(output_file)
        
        pdf_merger.close()
        os.unlink(temp_cover_pdf)
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_overall_summary_pdf(config_path_or_dict, output_pdf=None):
    """Generate a PDF report from the overall summary JSON."""
    try:
        if isinstance(config_path_or_dict, dict):
            config = config_path_or_dict
        else:
            with open(config_path_or_dict, 'r') as f:
                config = json.load(f) if str(config_path_or_dict).endswith('.json') else yaml.safe_load(f)
        
        translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
        translator = TranslationManager(translations_dir, default_language='en')
        translator.set_language(config.get('output_language', 'en'))
        
        output_location = config['output_location']
        summary_file = os.path.join(output_location, 'data_files', 'overall_summary.json')
        
        if not os.path.exists(summary_file):
            raise FileNotFoundError(f"Overall summary file not found: {summary_file}")
            
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
            
        if output_pdf is None:
            current_date = datetime.now().strftime('%Y%m%d')
            output_pdf = os.path.join(output_location, 'records', f'overall_summary_{current_date}.pdf')
            
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        
        doc = SimpleDocTemplate(
            output_pdf,
            pagesize=letter,
            rightMargin=1*inch,
            leftMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
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
        
        story = []
        
        story.append(Paragraph("Medical Records Summary", title_style))
        story.append(Paragraph(datetime.now().strftime('%Y-%m-%d'), normal_style))
        story.append(Spacer(1, 30))
        
        for section_name, section_data in summary_data.items():
            heading = section_name.replace('_', ' ').title()
            story.append(Paragraph(heading, heading_style))
            
            content = section_data.get('section', '')
            
            if isinstance(content, str):
                story.append(Paragraph(content, normal_style))
            elif isinstance(content, list):
                for item in content:
                    story.append(Paragraph(f"• {item}", bullet_style))
            
            story.append(Spacer(1, 20))
            
            if isinstance(section_data, dict) and 'summary' in section_data:
                story.append(Paragraph("Summary", heading_style))
                story.append(Paragraph(section_data['summary'], normal_style))
                story.append(Spacer(1, 20))
        
        doc.build(story)
        
        return output_pdf
        
    except Exception as e:
        logging.error(f"Error generating overall summary PDF: {str(e)}")
        raise
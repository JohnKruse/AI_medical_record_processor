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
       - Insert short summary PDF right after cover page
       - Table of contents
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
        
        # Get privacy notice - use config if not blank, otherwise use translation
        privacy_notice = config.get('privacy_notice', '').strip()
        if not privacy_notice:
            privacy_notice = translator.get('privacy_notice')
        
        # Load and sort records by treatment date
        df = pd.read_csv(data_file)
        df['treatment_date'] = pd.to_datetime(df['treatment_date'], errors='coerce')
        df = df.sort_values('treatment_date', ascending=False)
        
        # Get mode of patient names
        lastname = df['patient_last_name'].mode().iloc[0]
        firstname = df['patient_first_name'].mode().iloc[0]
        
        # Create a temporary PDF for the cover + TOC
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
        privacy_style = ParagraphStyle(
            'PrivacyNotice',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1  # Center alignment
        )
        
        # Build PDF content
        story = []
        
        # Cover page
        patient_name = lastname if not pd.isna(lastname) else translator.get('status.unknown')
        patient_fname = firstname if not pd.isna(firstname) else ""
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        story.append(Paragraph(f"{translator.get('pdf.medical_records')}<br/><br/>{patient_name}, {patient_fname}", title_style))
        story.append(Paragraph(current_date, title_style))
        story.append(Spacer(1, 30))  # Add space before privacy notice
        story.append(Paragraph(privacy_notice, privacy_style))
        story.append(PageBreak())
        
        # Table of contents
        story.append(Paragraph(translator.get('pdf.records_included'), heading_style))
        
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
        
        # Insert short summary PDF after cover page and before TOC
        output_short_summary_pdf = config.get('output_short_summary_pdf', 'overall_short_summary.pdf')
        summary_pdf_path = os.path.join(output_location, output_short_summary_pdf)
        
        cover_reader = PyPDF2.PdfReader(temp_cover_pdf)
        
        # Append only the first page (cover page)
        temp_cover_page = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
        cover_writer = PyPDF2.PdfWriter()
        cover_writer.add_page(cover_reader.pages[0])
        with open(temp_cover_page, 'wb') as cover_f:
            cover_writer.write(cover_f)
        
        pdf_merger.append(temp_cover_page)
        os.unlink(temp_cover_page)
        
        # Append the summary PDF
        if os.path.exists(summary_pdf_path):
            pdf_merger.append(summary_pdf_path)
        else:
            logging.warning(f"Short summary PDF not found at: {summary_pdf_path}")
        
        # Append the rest of the TOC pages (if any)
        if len(cover_reader.pages) > 1:
            temp_toc = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
            toc_writer = PyPDF2.PdfWriter()
            for p in range(1, len(cover_reader.pages)):
                toc_writer.add_page(cover_reader.pages[p])
            with open(temp_toc, 'wb') as toc_f:
                toc_writer.write(toc_f)
            pdf_merger.append(temp_toc)
            os.unlink(temp_toc)
        
        os.unlink(temp_cover_pdf)
        
        # Add each doc with its cover
        for i, (_, record) in enumerate(df.iterrows(), 1):
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
                 str(record['treatment_date']) if pd.notna(record['treatment_date']) else translator.get('status.unknown')),
                (translator.get('fields.visit_type'), 
                 str(record['visit_type']) if pd.notna(record['visit_type']) else translator.get('status.unknown')),
                (translator.get('fields.provider_name'), 
                 str(record['provider_name']) if pd.notna(record['provider_name']) else translator.get('status.unknown')),
                (translator.get('fields.provider_facility'), 
                 str(record['provider_facility']) if pd.notna(record['provider_facility']) else translator.get('status.unknown')),
                (translator.get('fields.primary_condition'), 
                 str(record['primary_condition']) if pd.notna(record['primary_condition']) else translator.get('status.unknown')),
                (translator.get('fields.summary'), 
                 str(record['summary']) if pd.notna(record['summary']) else translator.get('status.unknown')),
                (translator.get('fields.test_results'), 
                 str(record['test_results']) if pd.notna(record['test_results']) else translator.get('status.unknown')),
                (translator.get('fields.diagnoses'), 
                 str(record['diagnoses']) if pd.notna(record['diagnoses']) else translator.get('status.unknown')),
                (translator.get('fields.treatments'), 
                 str(record['treatments']) if pd.notna(record['treatments']) else translator.get('status.unknown'))
            ]
            
            for label, value in record_info:
                story.append(Paragraph(f"<b>{label}:</b> {value}", normal_style))
                story.append(Spacer(1, 12))
            
            story.append(Spacer(1, 30))  # Add space before privacy notice
            story.append(Paragraph(privacy_notice, privacy_style))
            
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
        
        # Get privacy notice - use config if not blank, otherwise use translation
        privacy_notice = config.get('privacy_notice', '').strip()
        if not privacy_notice:
            privacy_notice = translator.get('privacy_notice')
        
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
        privacy_style = ParagraphStyle(
            'PrivacyNotice',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1  # Center alignment
        )
        
        story = []
        
        story.append(Paragraph("Medical Records Summary", title_style))
        story.append(Paragraph(datetime.now().strftime('%Y-%m-%d'), normal_style))
        story.append(Spacer(1, 30))
        
        for section_name, section_data in summary_data.items():
            heading = section_name.replace('_', ' ').title()
            story.append(Paragraph(heading, heading_style))
            
            if isinstance(section_data, dict):
                content = section_data.get('section', '')
                if isinstance(content, str):
                    story.append(Paragraph(content, normal_style))
                elif isinstance(content, list):
                    for item in content:
                        story.append(Paragraph(f"• {item}", bullet_style))
                
                if 'summary' in section_data:
                    story.append(Paragraph("Summary", heading_style))
                    summary_content = section_data['summary']
                    if isinstance(summary_content, list):
                        for item in summary_content:
                            story.append(Paragraph(str(item), normal_style))
                    else:
                        story.append(Paragraph(str(summary_content), normal_style))
            else:
                if isinstance(section_data, list):
                    for item in section_data:
                        story.append(Paragraph(str(item), normal_style))
                else:
                    story.append(Paragraph(str(section_data), normal_style))
            
            story.append(Spacer(1, 20))
        
        story.append(Spacer(1, 30))  # Add space before privacy notice
        story.append(Paragraph(privacy_notice, privacy_style))
        
        doc.build(story)
        
        return output_pdf
        
    except Exception as e:
        logging.error(f"Error generating overall summary PDF: {str(e)}")
        raise
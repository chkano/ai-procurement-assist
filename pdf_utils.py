# pdf_utils.py

import io
import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def format_field_name(field_name):
    """Formats field names from snake_case to Title Case and provides translations."""
    # Convert snake_case to Title Case
    formatted = field_name.replace('_', ' ').title()

    # Dictionary for common translations
    translations = {
        'Company Name': 'ชื่อบริษัท / Company Name',
        'Company Address': 'ที่อยู่บริษัท / Address',
        'Company Contact': 'ติดต่อ / Contact',
        'Company Phone': 'โทรศัพท์ / Phone',
        'Vendor Name': 'ชื่อผู้ขาย / Vendor Name',
        'Total Price': 'ราคารวม / Total Price',
        'Unit Price': 'ราคาต่อหน่วย / Unit Price',
        'Quantity': 'จำนวน / Quantity',
        'Description': 'รายละเอียด / Description',
        'Payment Terms': 'เงื่อนไขการชำระเงิน / Payment Terms',
        'Delivery Date': 'วันที่จัดส่ง / Delivery Date',
        'Purchase Order': 'ใบสั่งซื้อ / Purchase Order',
        'Requirements': 'ความต้องการ / Requirements',
        'Generated At': 'สร้างเมื่อ / Generated At'
    }

    return translations.get(formatted, formatted)

def create_pdf_document(content, title, doc_type="RFQ"):
    """Creates a PDF document with professional formatting."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = []

    # Define custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['h1'], fontSize=18, spaceAfter=20, textColor=colors.HexColor("#000080"))
    heading_style = ParagraphStyle('CustomHeading', parent=styles['h2'], fontSize=12, spaceAfter=10, textColor=colors.HexColor("#4682B4"))
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, spaceAfter=8)

    # Add title
    story.append(Paragraph(f"{doc_type}: {title}", title_style))
    story.append(Spacer(1, 0.25 * inch))

    # Process content
    if isinstance(content, dict):
        # Special handling for JSON content if it's nested
        json_content_str = content.get('content', '{}')
        try:
            # Try to parse the content string as JSON
            json_content = json.loads(json_content_str) if isinstance(json_content_str, str) else json_content_str
            story.extend(create_tables_from_json(json_content, normal_style, heading_style))
        except (json.JSONDecodeError, TypeError):
            # If it fails, treat it as plain text
            if json_content_str:
                story.append(Paragraph("Content:", heading_style))
                story.append(Paragraph(str(json_content_str).replace('\n', '<br/>'), normal_style))
    elif isinstance(content, str):
         story.append(Paragraph(content, normal_style))


    story.append(Spacer(1, 0.5 * inch))
    footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(Paragraph(footer_text, styles['Italic']))

    doc.build(story)
    buffer.seek(0)
    return buffer

def create_tables_from_json(json_data, normal_style, heading_style):
    """Converts nested JSON data into a series of formatted tables for a PDF."""
    story = []
    if not isinstance(json_data, dict):
        return story

    for section_key, section_value in json_data.items():
        story.append(Paragraph(format_field_name(section_key), heading_style))

        if isinstance(section_value, list) and section_value and isinstance(section_value[0], dict):
            # Creates a table for a list of dictionaries (like line items)
            all_keys = sorted(section_value[0].keys())
            headers = [format_field_name(key) for key in all_keys]
            table_data = [headers]
            for item in section_value:
                row = [str(item.get(key, '')) for key in all_keys]
                table_data.append(row)

            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4682B4")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E6E6FA")),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)

        elif isinstance(section_value, dict):
             # Creates a key-value table
            table_data = [[format_field_name(k), str(v)] for k, v in section_value.items()]
            table = Table(table_data, colWidths=[2 * inch, 4 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ]))
            story.append(table)
        else:
            story.append(Paragraph(str(section_value), normal_style))

        story.append(Spacer(1, 0.2 * inch))
    return story


def create_comparison_table_pdf(quotations_data):
    """Creates a PDF comparing items across different vendor quotations."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph("Vendor Quotation Comparison", styles['h1']), Spacer(1, 20)]

    if quotations_data:
        vendors = list(quotations_data.keys())
        # Aggregate all unique items and their prices from all vendors
        comparison_data = {}
        for vendor, data in quotations_data.items():
            if data and 'items' in data and isinstance(data['items'], list):
                for item in data['items']:
                    desc = item.get('description', 'N/A')
                    price = item.get('total_price', item.get('unit_price', 'N/A'))
                    if desc not in comparison_data:
                        comparison_data[desc] = {v: 'N/A' for v in vendors}
                    comparison_data[desc][vendor] = price

        # Prepare data for the table
        header = ['Item Description'] + vendors
        table_data = [header]
        for item, prices in comparison_data.items():
            row = [item] + [prices[v] for v in vendors]
            table_data.append(row)

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer
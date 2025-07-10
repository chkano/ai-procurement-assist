import io
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Assuming pdf_utils.py is refactored into this file
app = FastAPI(
    title="PDF Generation Service",
    description="Generates professional PDF documents from JSON data.",
)

class PdfRequest(BaseModel):
    content: Dict[str, Any]
    title: str
    doc_type: str

class ComparisonPdfRequest(BaseModel):
    quotations_data: Dict[str, Any]


def format_field_name(field_name):
    formatted = field_name.replace('_', ' ').title()
    translations = {
        'Company Name': 'ชื่อบริษัท / Company Name', 'Company Address': 'ที่อยู่บริษัท / Address',
        'Company Contact': 'ติดต่อ / Contact', 'Company Phone': 'โทรศัพท์ / Phone',
        'Vendor Name': 'ชื่อผู้ขาย / Vendor Name', 'Total Price': 'ราคารวม / Total Price',
        'Unit Price': 'ราคาต่อหน่วย / Unit Price', 'Quantity': 'จำนวน / Quantity',
        'Description': 'รายละเอียด / Description', 'Payment Terms': 'เงื่อนไขการชำระเงิน / Payment Terms',
        'Delivery Date': 'วันที่จัดส่ง / Delivery Date', 'Purchase Order': 'ใบสั่งซื้อ / Purchase Order',
        'Requirements': 'ความต้องการ / Requirements', 'Generated At': 'สร้างเมื่อ / Generated At'
    }
    return translations.get(formatted, formatted)

def create_tables_from_json(json_data, normal_style, heading_style):
    story = []
    if not isinstance(json_data, dict): return story
    for section_key, section_value in json_data.items():
        story.append(Paragraph(format_field_name(section_key), heading_style))
        if isinstance(section_value, list) and section_value and isinstance(section_value[0], dict):
            all_keys = sorted(section_value[0].keys())
            headers = [format_field_name(key) for key in all_keys]
            table_data = [headers] + [[str(item.get(key, '')) for key in all_keys] for item in section_value]
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4682B4")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12), ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#E6E6FA")),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
            story.append(table)
        elif isinstance(section_value, dict):
            table_data = [[format_field_name(k), str(v)] for k, v in section_value.items()]
            table = Table(table_data, colWidths=[2 * inch, 4 * inch])
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black), ('ALIGN', (0, 0), (-1, -1), 'LEFT')]))
            story.append(table)
        else: story.append(Paragraph(str(section_value), normal_style))
        story.append(Spacer(1, 0.2 * inch))
    return story

@app.post("/generate-standard-pdf", summary="Generate a standard document PDF")
def generate_standard_pdf(request: PdfRequest):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = []
    title_style = ParagraphStyle('CustomTitle', parent=styles['h1'], fontSize=18, spaceAfter=20, textColor=colors.HexColor("#000080"))
    heading_style = ParagraphStyle('CustomHeading', parent=styles['h2'], fontSize=12, spaceAfter=10, textColor=colors.HexColor("#4682B4"))
    normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, spaceAfter=8)
    story.append(Paragraph(f"{request.doc_type}: {request.title}", title_style))
    story.append(Spacer(1, 0.25 * inch))
    
    json_content_str = request.content.get('content', '{}')
    try:
        json_content = json.loads(json_content_str) if isinstance(json_content_str, str) else json_content_str
        story.extend(create_tables_from_json(json_content, normal_style, heading_style))
    except (json.JSONDecodeError, TypeError):
        story.append(Paragraph("Content:", heading_style))
        story.append(Paragraph(str(json_content_str).replace('\n', '<br/>'), normal_style))

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Italic']))
    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=document.pdf"})


@app.post("/generate-comparison-pdf", summary="Generate a vendor comparison PDF")
def generate_comparison_pdf(request: ComparisonPdfRequest):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph("Vendor Quotation Comparison", styles['h1']), Spacer(1, 20)]
    
    quotations_data = request.quotations_data
    if quotations_data:
        vendors = list(quotations_data.keys())
        comparison_data = {}
        for vendor, data in quotations_data.items():
            if data and 'items' in data and isinstance(data['items'], list):
                for item in data['items']:
                    desc = item.get('description', 'N/A')
                    price = item.get('total_price', item.get('unit_price', 'N/A'))
                    if desc not in comparison_data:
                        comparison_data[desc] = {v: 'N/A' for v in vendors}
                    comparison_data[desc][vendor] = price
        header = ['Item Description'] + vendors
        table_data = [header] + [[item] + [prices[v] for v in vendors] for item, prices in comparison_data.items()]
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        story.append(table)
    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=comparison.pdf"})
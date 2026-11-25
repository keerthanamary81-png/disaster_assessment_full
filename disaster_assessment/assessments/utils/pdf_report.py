"""
PDF Report Generation using ReportLab
"""
import os
from pathlib import Path
from datetime import datetime
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas


def generate_assessment_pdf(assessment):
    try:
        reports_dir = Path(settings.MEDIA_ROOT) / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        filename = f"report_{assessment.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = reports_dir / filename

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='MainTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=HexColor('#0d47a1'),
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        styles.add(ParagraphStyle(
            name='SubTitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor('#546e7a'),
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        styles.add(ParagraphStyle(
            name='SectionHead',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=HexColor('#1565c0'),
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        styles.add(ParagraphStyle(
            name='BodyText',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY
        ))
        styles.add(ParagraphStyle(
            name='Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#c62828'),
            alignment=TA_CENTER,
            spaceBefore=10
        ))
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#78909c'),
            alignment=TA_CENTER
        ))

        story = []

        # Header
        story.append(Paragraph("AI-BASED DISASTER DAMAGE ASSESSMENT REPORT", styles['MainTitle']))
        story.append(Paragraph("Preliminary Visual Analysis System", styles['SubTitle']))
        story.append(HRFlowable(width="100%", thickness=2, color=HexColor('#1565c0'), spaceAfter=12))

        # Meta info table
        img_obj = assessment.image
        meta_data = [
            ['Report ID:', f"ASR-{assessment.id:05d}"],
            ['Generated On:', assessment.created_at.strftime('%d %B %Y, %H:%M IST')],
            ['Disaster Type:', img_obj.get_disaster_type_display()],
            ['Affected Location:', img_obj.location],
            ['Incident Date:', str(img_obj.date_of_incident)],
            ['Uploaded By:', img_obj.user.get_full_name() or img_obj.user.username],
            ['AI Model:', assessment.model_version],
            ['Processing Time:', f"{assessment.processing_time} seconds"],
            ['Overall Severity:', assessment.get_overall_severity_display().upper()],
        ]
        meta_table = Table(meta_data, colWidths=[4.5*cm, 11*cm])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#37474f')),
            ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#212121')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f5f7fa')),
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#cfd8dc')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # Images section
        story.append(Paragraph("1. Image Analysis", styles['SectionHead']))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#90caf9'), spaceAfter=8))

        img_paths = []
        if img_obj.image and os.path.exists(img_obj.image.path):
            img_paths.append(('Original Image', img_obj.image.path))
        if assessment.analysed_image and os.path.exists(assessment.analysed_image.path):
            img_paths.append(('AI Annotated Image', assessment.analysed_image.path))

        if img_paths:
            img_elements = []
            for title, path in img_paths:
                try:
                    # Resize for PDF
                    pil_img = Image(path, width=7.5*cm, height=5.5*cm, kind='proportional')
                    img_elements.append([Paragraph(f"<b>{title}</b>", styles['BodyText']), pil_img])
                except Exception:
                    img_elements.append([Paragraph(f"<b>{title}</b> (unavailable)", styles['BodyText']), ''])

            if len(img_elements) == 2:
                img_table = Table([
                    [img_elements[0][0], img_elements[1][0]],
                    [img_elements[0][1], img_elements[1][1]]
                ], colWidths=[8*cm, 8*cm])
            else:
                img_table = Table([[img_elements[0][0]], [img_elements[0][1]]], colWidths=[16*cm])
            img_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(img_table)
        story.append(Spacer(1, 10))

        # Detection results
        story.append(Paragraph("2. Detected Damage Categories", styles['SectionHead']))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#90caf9'), spaceAfter=8))

        detections = assessment.detections.all()
        if detections:
            det_data = [['Category', 'Confidence', 'Count / Label']]
            for d in detections:
                det_data.append([
                    d.get_category_display(),
                    f"{d.confidence_percent}%",
                    d.label or str(d.count)
                ])
            det_table = Table(det_data, colWidths=[7*cm, 3.5*cm, 5.5*cm])
            det_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1565c0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.4, HexColor('#bbdefb')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#e3f2fd'), white]),
            ]))
            story.append(det_table)
        else:
            story.append(Paragraph("No specific damage objects were detected by the model for the supported categories.", styles['BodyText']))

        story.append(Spacer(1, 10))

        # Summary
        story.append(Paragraph("3. Assessment Summary", styles['SectionHead']))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#90caf9'), spaceAfter=8))
        story.append(Paragraph(assessment.summary or "No summary available.", styles['BodyText']))

        if img_obj.description:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>User Notes:</b> " + img_obj.description, styles['BodyText']))

        # Disclaimer
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor('#ef5350'), spaceAfter=6))
        story.append(Paragraph(
            "DISCLAIMER: This report is generated by an AI visual analysis system and provides only a preliminary indication of visible damage. "
            "It does NOT assess structural integrity, safety, or suitability for habitation. "
            "All findings must be verified by qualified disaster response professionals, structural engineers, and local authorities before any decision-making.",
            styles['Disclaimer']
        ))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            "© Disaster Damage Assessment System | For official use by authorised response teams only",
            styles['Footer']
        ))

        doc.build(story)
        return f"reports/{filename}"
    except Exception as e:
        print(f"PDF generation error: {e}")
        return None

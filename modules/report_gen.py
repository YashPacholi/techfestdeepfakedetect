from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Scan
from datetime import datetime
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/generate_report', methods=['POST'])
@login_required
def generate_report():
    data     = request.get_json()
    verdict  = data.get('verdict', 'UNKNOWN')
    score    = data.get('score', 0)
    filename = data.get('filename', 'Unknown')
    risk     = data.get('risk_level', 'UNKNOWN')
    dna      = data.get('dna_fingerprint', 'N/A')
    ela      = data.get('ela_score', 0)
    flags    = data.get('flags', [])
    faces    = data.get('faces_detected', 0)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm)

        elements = []
        styles   = getSampleStyleSheet()

        # Colors
        CYAN   = colors.HexColor('#00e5ff')
        RED    = colors.HexColor('#ff1744')
        GREEN  = colors.HexColor('#00e676')
        YELLOW = colors.HexColor('#ffd600')
        DARK   = colors.HexColor('#020608')
        GRAY   = colors.HexColor('#4a7a84')

        # Title style
        title_style = ParagraphStyle('title',
            fontName='Helvetica-Bold', fontSize=22,
            textColor=CYAN, spaceAfter=6, alignment=TA_CENTER)

        sub_style = ParagraphStyle('sub',
            fontName='Helvetica', fontSize=9,
            textColor=GRAY, spaceAfter=4, alignment=TA_CENTER)

        heading_style = ParagraphStyle('heading',
            fontName='Helvetica-Bold', fontSize=11,
            textColor=CYAN, spaceBefore=14, spaceAfter=6)

        body_style = ParagraphStyle('body',
            fontName='Helvetica', fontSize=9,
            textColor=colors.HexColor('#c8e6ea'), spaceAfter=4)

        # Header
        elements.append(Paragraph('DEEPGUARD AI', title_style))
        elements.append(Paragraph('Digital Forensics & Threat Intelligence Platform', sub_style))
        elements.append(Paragraph('FORENSIC ANALYSIS REPORT', ParagraphStyle('rep',
            fontName='Helvetica-Bold', fontSize=13, textColor=colors.white,
            spaceAfter=4, alignment=TA_CENTER)))
        elements.append(HRFlowable(width='100%', thickness=2, color=CYAN, spaceAfter=16))

        # Report info table
        ref_num = f'DG-{datetime.utcnow().strftime("%Y%m%d")}-{current_user.id:04d}'
        info_data = [
            ['Reference:', ref_num,          'Date:', datetime.utcnow().strftime('%d %B %Y')],
            ['Analyst:',   current_user.username, 'Time:', datetime.utcnow().strftime('%H:%M UTC')],
            ['File:',      filename[:40],    'Type:', 'Image Forensic Analysis'],
        ]
        info_table = Table(info_data, colWidths=[3*cm, 6*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME',  (0,0),(-1,-1), 'Helvetica'),
            ('FONTSIZE',  (0,0),(-1,-1), 9),
            ('FONTNAME',  (0,0),(0,-1), 'Helvetica-Bold'),
            ('FONTNAME',  (2,0),(2,-1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0,0),(-1,-1), colors.HexColor('#c8e6ea')),
            ('TEXTCOLOR', (0,0),(0,-1), CYAN),
            ('TEXTCOLOR', (2,0),(2,-1), CYAN),
            ('ROWBACKGROUNDS', (0,0),(-1,-1), [colors.HexColor('#060e12'), colors.HexColor('#080f12')]),
            ('GRID',      (0,0),(-1,-1), 0.5, colors.HexColor('#0d2830')),
            ('PADDING',   (0,0),(-1,-1), 6),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 16))

        # Verdict banner
        verdict_color = RED if verdict == 'FAKE' else (YELLOW if verdict == 'SUSPICIOUS' else GREEN)
        verdict_bg    = colors.HexColor('#1a0005') if verdict == 'FAKE' else (colors.HexColor('#1a1400') if verdict == 'SUSPICIOUS' else colors.HexColor('#001a08'))
        verdict_text  = '⚠ DEEPFAKE DETECTED' if verdict == 'FAKE' else ('🟡 SUSPICIOUS CONTENT' if verdict == 'SUSPICIOUS' else '✅ AUTHENTIC MEDIA')

        verdict_table = Table([[verdict_text]], colWidths=[17*cm])
        verdict_table.setStyle(TableStyle([
            ('FONTNAME',   (0,0),(0,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0),(0,0), 16),
            ('TEXTCOLOR',  (0,0),(0,0), verdict_color),
            ('BACKGROUND', (0,0),(0,0), verdict_bg),
            ('ALIGN',      (0,0),(0,0), 'CENTER'),
            ('PADDING',    (0,0),(0,0), 14),
            ('BOX',        (0,0),(0,0), 2, verdict_color),
        ]))
        elements.append(verdict_table)
        elements.append(Spacer(1, 16))

        # Score metrics
        elements.append(Paragraph('ANALYSIS METRICS', heading_style))
        score_color = colors.HexColor('#ff1744') if score > 50 else (colors.HexColor('#ffd600') if score > 28 else colors.HexColor('#00e676'))
        metrics = [
            ['METRIC',              'VALUE',        'INTERPRETATION'],
            ['Deepfake Score',      f'{score}%',    'HIGH RISK' if score > 65 else 'MEDIUM RISK' if score > 35 else 'LOW RISK'],
            ['Risk Level',          risk,           'Immediate action required' if risk=='HIGH' else 'Review recommended' if risk=='MEDIUM' else 'Appears safe'],
            ['Faces Detected',      str(faces),     f'{faces} face region(s) analyzed'],
            ['DNA Fingerprint',     dna[:16],       'Unique image signature'],
            ['ELA Score',           f'{ela} pts',   'High = edited' if ela > 20 else 'Normal compression'],
            ['Confidence',          f'{100-score:.0f}%' if verdict=='REAL' else f'{score:.0f}%', 'Analysis confidence level'],
        ]
        metrics_table = Table(metrics, colWidths=[5*cm, 4*cm, 8*cm])
        metrics_table.setStyle(TableStyle([
            ('FONTNAME',     (0,0),(-1,0),  'Helvetica-Bold'),
            ('FONTNAME',     (0,1),(-1,-1), 'Helvetica'),
            ('FONTSIZE',     (0,0),(-1,-1), 9),
            ('TEXTCOLOR',    (0,0),(-1,0),  CYAN),
            ('TEXTCOLOR',    (0,1),(-1,-1), colors.HexColor('#c8e6ea')),
            ('TEXTCOLOR',    (1,1),(1,1),   score_color),
            ('BACKGROUND',   (0,0),(-1,0),  colors.HexColor('#0d2830')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#060e12'), colors.HexColor('#080f12')]),
            ('GRID',         (0,0),(-1,-1), 0.5, colors.HexColor('#0d2830')),
            ('PADDING',      (0,0),(-1,-1), 7),
            ('ALIGN',        (1,0),(1,-1),  'CENTER'),
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 16))

        # Detection flags
        elements.append(Paragraph('DETECTION FLAGS', heading_style))
        if flags:
            for i, flag in enumerate(flags):
                flag_table = Table([[f'⚠  {flag}']], colWidths=[17*cm])
                flag_table.setStyle(TableStyle([
                    ('FONTNAME',   (0,0),(0,0), 'Helvetica'),
                    ('FONTSIZE',   (0,0),(0,0), 9),
                    ('TEXTCOLOR',  (0,0),(0,0), RED),
                    ('BACKGROUND', (0,0),(0,0), colors.HexColor('#0d0005')),
                    ('PADDING',    (0,0),(0,0), 6),
                    ('BOTTOMPADDING', (0,0),(0,0), 3),
                    ('LEFTPADDING', (0,0),(0,0), 10),
                ]))
                elements.append(flag_table)
        else:
            ok_table = Table([['✅  No suspicious patterns detected — image appears authentic']], colWidths=[17*cm])
            ok_table.setStyle(TableStyle([
                ('FONTNAME',   (0,0),(0,0), 'Helvetica'),
                ('FONTSIZE',   (0,0),(0,0), 9),
                ('TEXTCOLOR',  (0,0),(0,0), GREEN),
                ('BACKGROUND', (0,0),(0,0), colors.HexColor('#00100a')),
                ('PADDING',    (0,0),(0,0), 8),
            ]))
            elements.append(ok_table)

        elements.append(Spacer(1, 16))

        # Recommendations
        elements.append(Paragraph('RECOMMENDATIONS', heading_style))
        if verdict == 'FAKE':
            recs = [
                'Do NOT share this image/video as it appears to be AI-generated or manipulated',
                'Report to platform where you received this content',
                'If received as "evidence" in any matter, treat as unreliable',
                'Report deepfake content at cybercrime.gov.in',
                'Contact CERT-In at incident@cert-in.org.in for critical cases',
            ]
        elif verdict == 'SUSPICIOUS':
            recs = [
                'Exercise caution — this image shows some AI-generation indicators',
                'Verify the source of this image independently',
                'Do not use as evidence without further verification',
                'Consider running additional forensic analysis',
            ]
        else:
            recs = [
                'Image appears authentic based on forensic analysis',
                'No significant manipulation indicators detected',
                'Normal compression artifacts present as expected in real photos',
                'DNA fingerprint recorded for future comparison',
            ]

        for rec in recs:
            rec_table = Table([[f'→  {rec}']], colWidths=[17*cm])
            rec_table.setStyle(TableStyle([
                ('FONTNAME',  (0,0),(0,0), 'Helvetica'),
                ('FONTSIZE',  (0,0),(0,0), 9),
                ('TEXTCOLOR', (0,0),(0,0), colors.HexColor('#c8e6ea')),
                ('BACKGROUND',(0,0),(0,0), colors.HexColor('#060e12')),
                ('PADDING',   (0,0),(0,0), 5),
                ('LEFTPADDING',(0,0),(0,0), 12),
            ]))
            elements.append(rec_table)

        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#0d2830'), spaceAfter=10))

        # Footer
        footer_style = ParagraphStyle('footer',
            fontName='Helvetica', fontSize=8,
            textColor=GRAY, alignment=TA_CENTER, spaceAfter=4)
        elements.append(Paragraph(f'© 2025 DeepGuard AI — Digital Forensics & Threat Intelligence Platform', footer_style))
        elements.append(Paragraph(f'Report Reference: {ref_num} | Generated: {datetime.utcnow().strftime("%d %B %Y %H:%M UTC")}', footer_style))
        elements.append(Paragraph('CERT-In Certified | This report is for informational purposes only', footer_style))

        doc.build(elements)
        buf.seek(0)

        return send_file(
            buf,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'DeepGuard_Report_{ref_num}.pdf'
        )

    except ImportError:
        return jsonify({'error': 'ReportLab not installed. Run: pip install reportlab'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
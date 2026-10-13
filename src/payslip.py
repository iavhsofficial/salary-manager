"""
PDF payslip generator using ReportLab.
"""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)

from src.config import (
    SCHOOL_NAME, PAYSLIP_TITLE, PAYSLIP_FOOTER, PAYSLIP_DIR
)


def safe_filename(name):
    """Turn a name into a safe filename."""
    return re.sub(r"[^\w\s-]", "", name).replace(" ", "_")


def format_amount(value):
    """Format a number as '12,345'."""
    try:
        return f"{float(value or 0):,.0f}"
    except (ValueError, TypeError):
        return "0"


def generate_payslip(staff, salary, month, year, open_after=False):
    """
    Generate a PDF payslip.

    staff:  dict with name, sr_no, doj, basic_pay
    salary: dict with writing, speaking, checking, dis, ct, od,
            ot_extra, e_day, la_adv, gp_fund, sec, s_sec, oab, sl,
            cl_day, ann_l, ab_fine, gross_pay, total_ded, net_pay,
            total_1, total_2, eda, fine, cl_fine
    """
    # ---- Prepare values ----
    name = staff.get("name", "Unknown")
    sr_no = staff.get("sr_no", "")
    doj = staff.get("doj", "")
    basic = float(staff.get("basic_pay", 0) or 0)

    writing = float(salary.get("writing", 0) or 0)
    speaking = float(salary.get("speaking", 0) or 0)
    total_1 = float(salary.get("total_1", basic + writing + speaking) or 0)

    checking = float(salary.get("checking", 0) or 0)
    dis = float(salary.get("dis", 0) or 0)
    ct = float(salary.get("ct", 0) or 0)
    od = float(salary.get("od", 0) or 0)
    total_2 = float(salary.get("total_2", checking + dis + ct + od) or 0)

    ot_extra = float(salary.get("ot_extra", 0) or 0)
    e_day = float(salary.get("e_day", 0) or 0)
    eda = float(salary.get("eda", 0) or 0)
    gross_pay = float(salary.get("gross_pay", 0) or 0)

    la_adv = float(salary.get("la_adv", 0) or 0)
    gp_fund = float(salary.get("gp_fund", 0) or 0)
    sec = float(salary.get("sec", 0) or 0)
    s_sec = float(salary.get("s_sec", 0) or 0)
    oab = float(salary.get("oab", 0) or 0)
    sl = float(salary.get("sl", 0) or 0)
    cl_day = float(salary.get("cl_day", 0) or 0)
    fine = float(salary.get("fine", 0) or 0)
    cl_fine = float(salary.get("cl_fine", 0) or 0)
    ann_l = float(salary.get("ann_l", 0) or 0)
    ab_fine = float(salary.get("ab_fine", 0) or 0)
    total_ded = float(salary.get("total_ded", 0) or 0)
    net_pay = float(salary.get("net_pay", 0) or 0)

    # ---- Output path ----
    output_path = PAYSLIP_DIR / f"{safe_filename(name)}_{month}_{year}.pdf"

    # ---- Build PDF ----
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Payslip - {name}",
    )

    styles = getSampleStyleSheet()
    story = []

    # ---- Header ----
    header_style = ParagraphStyle(
        "HeaderStyle", parent=styles["Title"], fontSize=15,
        textColor=colors.HexColor("#1a3a6b"), alignment=1, spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        "SubStyle", parent=styles["Normal"], fontSize=11,
        textColor=colors.HexColor("#1a3a6b"), alignment=1, spaceAfter=8,
    )
    story.append(Paragraph(SCHOOL_NAME, header_style))
    story.append(Paragraph(
        f"{PAYSLIP_TITLE} — {month.upper()} {year}", sub_style
    ))
    story.append(Spacer(1, 4))

    # ---- Employee info ----
    info = Table(
        [["Sr #", str(sr_no), "Name", name, "D.O.J", str(doj)]],
        colWidths=[15 * mm, 20 * mm, 20 * mm, 70 * mm, 20 * mm, 30 * mm],
    )
    info.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, 0), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, 0), "Helvetica-Bold", 9),
        ("FONT", (4, 0), (4, 0), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#1a3a6b")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(info)
    story.append(Spacer(1, 10))

    # ---- Earnings / Deductions side by side ----
    earnings_rows = [
        ["EARNINGS", "Rs."],
        ["Basic Pay", format_amount(basic)],
        ["Writing", format_amount(writing)],
        ["Speaking", format_amount(speaking)],
        ["Total # 1", format_amount(total_1)],
        ["Checking", format_amount(checking)],
        ["DIS", format_amount(dis)],
        ["C.T", format_amount(ct)],
        ["O.D", format_amount(od)],
        ["Total # 2", format_amount(total_2)],
        ["O.T / Extra", format_amount(ot_extra)],
        ["E Day", format_amount(e_day)],
        ["EDA", format_amount(eda)],
        ["Gross Pay", format_amount(gross_pay)],
    ]

    deductions_rows = [
        ["DEDUCTIONS", "Rs."],
        ["LA / Adv / Fine", format_amount(la_adv)],
        ["G.P Fund", format_amount(gp_fund)],
        ["Sec", format_amount(sec)],
        ["S.Sec", format_amount(s_sec)],
        ["OAB", format_amount(oab)],
        ["S.L", format_amount(sl)],
        ["Fine", format_amount(fine)],
        ["C.L Day", format_amount(cl_day)],
        ["C.L Fine", format_amount(cl_fine)],
        ["Ann. L", format_amount(ann_l)],
        ["AB Fine", format_amount(ab_fine)],
        ["Total Ded", format_amount(total_ded)],
    ]

    t_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a6b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 10),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#1a3a6b")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f5f7fb")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])

    t_earn = Table(earnings_rows, colWidths=[45 * mm, 30 * mm])
    t_earn.setStyle(t_style)

    t_ded = Table(deductions_rows, colWidths=[45 * mm, 30 * mm])
    t_ded.setStyle(t_style)

    side = Table(
        [[t_earn, "", t_ded]],
        colWidths=[78 * mm, 8 * mm, 78 * mm],
    )
    side.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(side)
    story.append(Spacer(1, 12))

    # ---- Net Pay highlight ----
    net_table = Table(
        [["NET PAY", f"Rs. {format_amount(net_pay)}"]],
        colWidths=[100 * mm, 60 * mm],
    )
    net_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1a3a6b")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONT", (0, 0), (0, 0), "Helvetica-Bold", 13),
        ("FONT", (1, 0), (1, 0), "Helvetica-Bold", 14),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(net_table)
    story.append(Spacer(1, 12))

    # ---- Footer ----
    footer_style = ParagraphStyle(
        "FooterStyle", parent=styles["Normal"], fontSize=7.5,
        textColor=colors.grey, alignment=1,
    )
    story.append(Paragraph(PAYSLIP_FOOTER, footer_style))

    doc.build(story)
    print(f"Payslip generated: {output_path}")
    return str(output_path)
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
    SCHOOL_NAME, PAYSLIP_TITLE, PAYSLIP_FOOTER, get_payslip_dir,
    ASSETS_DIR
)


def safe_filename(name):
    """Turn a name into a safe filename."""
    return re.sub(r"[^\w\s-]", "", name).replace(" ", "_")


def fmt(value):
    """Format a number as '12,345'."""
    try:
        return f"{float(value or 0):,.0f}"
    except (ValueError, TypeError):
        return "0"


def fmt_hrs(value):
    """Format hours/counts (integers)."""
    try:
        v = float(value or 0)
        return f"{int(v)}" if v == int(v) else f"{v:,.2f}"
    except (ValueError, TypeError):
        return "0"


def generate_payslip(staff, salary, month, year, open_after=False):
    """
    Generate a PDF payslip.

    staff:  dict with name, sr_no, date_of_joining, basic_pay, payment_mode,
            bank_name, bank_account, department, designation
    salary: dict with all salary fields (see calculations.calculate_salary)
    """
    # ---- Extract values ----
    name = staff.get("name", "Unknown")
    sr_no = staff.get("sr_no", "")
    doj = staff.get("date_of_joining", "")
    basic = float(staff.get("basic_pay", 0) or 0)
    dept = staff.get("department", "")
    desig = staff.get("designation", "")
    pay_mode = staff.get("payment_mode", "Cash")

    writing = float(salary.get("writing", 0) or 0)
    speaking = float(salary.get("speaking", 0) or 0)
    checking = float(salary.get("checking", 0) or 0)
    class_teacher = float(salary.get("class_teacher", 0) or 0)
    coordination = float(salary.get("coordination", 0) or 0)
    previous_pay = float(salary.get("previous_pay", 0) or 0)
    increment = float(salary.get("increment", 0) or 0)
    overtime = float(salary.get("overtime_allowance", 0) or 0)
    gross_pay = float(salary.get("gross_pay", 0) or 0)

    no_late = int(salary.get("no_late_arrivals", 0) or 0)
    late_ded = float(salary.get("late_arrival_deduction", 0) or 0)
    no_short = int(salary.get("no_short_leaves", 0) or 0)
    short_ded = float(salary.get("short_leave_deduction", 0) or 0)
    no_leave = int(salary.get("no_leaves", 0) or 0)
    leave_ded = float(salary.get("leaves_deduction", 0) or 0)
    absentee = float(salary.get("absentee_deduction", 0) or 0)

    gp_fund = float(salary.get("gp_fund", 0) or 0)
    social_sec = float(salary.get("social_security", 0) or 0)
    security = float(salary.get("security_deduction", 0) or 0)
    oab = float(salary.get("oab", 0) or 0)
    total_ded = float(salary.get("total_deductions", 0) or 0)
    net_pay = float(salary.get("net_pay", 0) or 0)

        # ---- Output path (month-wise folder) ----
    month_folder = get_payslip_dir(month, year)
    output_path = month_folder / f"{safe_filename(name)}.pdf"
    
    # ---- Build PDF ----
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Payslip - {name}",
    )

    styles = getSampleStyleSheet()
    story = []

    # ---- Logo (if available) ----
    logo_path = ASSETS_DIR / "school_logo.png"
    if logo_path.exists():
        try:
            from reportlab.platypus import Image
            logo = Image(str(logo_path), width=25*mm, height=25*mm)
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, 4))
        except Exception as e:
            print(f"Logo load failed: {e}")

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
        [
            ["Sr #", str(sr_no), "Name", name, "D.O.J", str(doj)],
            ["Dept", dept, "Designation", desig,
             "Payment", pay_mode],
        ],
        colWidths=[15 * mm, 20 * mm, 22 * mm, 68 * mm, 20 * mm, 30 * mm],
    )
    info.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("FONT", (4, 0), (4, -1), "Helvetica-Bold", 9),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e8eef7")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#1a3a6b")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(info)
    story.append(Spacer(1, 10))

    # ---- Earnings (left) ----
    earnings_rows = [
        ["EARNINGS", "Rs."],
        ["Basic Pay", fmt(basic)],
        ["Writing", fmt(writing)],
        ["Speaking", fmt(speaking)],
        ["Checking", fmt(checking)],
        ["Class Teacher", fmt(class_teacher)],
        ["Coordination", fmt(coordination)],
        ["Previous Pay", fmt(previous_pay)],
        ["Increment", fmt(increment)],
        ["Overtime", fmt(overtime)],
        ["", ""],
        ["GROSS PAY", fmt(gross_pay)],
    ]

    # ---- Deductions (right) ----
    deductions_rows = [
        ["DEDUCTIONS", "Rs."],
        [f"Late Arrivals ({no_late})", fmt(late_ded)],
        [f"Short Leaves ({no_short})", fmt(short_ded)],
        [f"Leaves ({no_leave})", fmt(leave_ded)],
        ["Absentee", fmt(absentee)],
        ["GP Fund", fmt(gp_fund)],
        ["Social Security", fmt(social_sec)],
        ["Security Ded.", fmt(security)],
        ["OAB", fmt(oab)],
        ["", ""],
        ["", ""],
        ["TOTAL DEDUCTIONS", fmt(total_ded)],
    ]

    # Common style
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

    # Highlight GROSS PAY and TOTAL DEDUCTIONS rows
    gross_row_idx = len(earnings_rows) - 1
    ded_row_idx = len(deductions_rows) - 1
    t_earn.setStyle(TableStyle([
        ("BACKGROUND", (0, gross_row_idx), (-1, gross_row_idx),
         colors.HexColor("#d4e4f7")),
        ("FONT", (0, gross_row_idx), (-1, gross_row_idx),
         "Helvetica-Bold", 10),
    ]))
    t_ded.setStyle(TableStyle([
        ("BACKGROUND", (0, ded_row_idx), (-1, ded_row_idx),
         colors.HexColor("#f7d4d4")),
        ("FONT", (0, ded_row_idx), (-1, ded_row_idx),
         "Helvetica-Bold", 10),
    ]))

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
    story.append(Spacer(1, 14))

    # ---- Net Pay highlight ----
    net_table = Table(
        [["NET PAY", f"Rs. {fmt(net_pay)}"]],
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
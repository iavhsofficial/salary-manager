"""
Reports tab — complete/cash/bank staff statements with print, Excel, PDF.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from src.config import (
    MONTHS, DEFAULT_MONTH, DEFAULT_YEAR,
    SCHOOL_NAME, get_payslip_dir, ASSETS_DIR
)

from src import database as db


REPORT_TYPES = [
    "All Staff Statement",
    "Cash in Hand",
    "Bank Only",
    "Bank Transfer Statement",
]


# All columns — (label, key, width_mm, align)
REPORT_COLUMNS = [
    ("Sr",          "sr_no",                  6,  "center"),
    ("Name",        "name",                   42, "w"),
    ("DOJ",         "date_of_joining",        22, "center"),
    ("Basic",       "basic_pay",              18, "e"),
    ("Writing",     "writing",                15, "e"),
    ("Speaking",    "speaking",               15, "e"),
    ("Checking",    "checking",               15, "e"),
    ("C.T",         "class_teacher",          15, "e"),
    ("Coord",       "coordination",           15, "e"),
    ("Prev. Pay",   "previous_pay",           18, "e"),
    ("Incr",        "increment",              15, "e"),
    ("Gross",       "gross_pay",              18, "e"),
    ("GPF",         "gp_fund",                12, "e"),
    ("N. Late",     "no_late_arrivals",       12, "center"),
    ("LA Ded",      "late_arrival_deduction", 15, "e"),
    ("N. SL",       "no_short_leaves",        10, "center"),
    ("SL Ded",      "short_leave_deduction",  15, "e"),
    ("N. Lv",       "no_leaves",              10, "center"),
    ("Lv Ded",      "leaves_deduction",       15, "e"),
    ("N. Abs",      "no_absentees",           12, "center"),
    ("Abs Ded",     "absentee_deduction",     15, "e"),
    ("Sec",         "security_deduction",     14, "e"),
    ("Already Ded", "security_already_deducted", 16, "e"),
    ("S.Sec",       "social_security",        14, "e"),
    ("OAB",         "oab",                    10, "e"),
    ("Misc Ded",    "misc_deduction",         15, "e"),
    ("Tot Ded",     "total_deductions",       18, "e"),
    ("OT Hrs/Days", "overtime_display",       16, "center"),
    ("OT Allow",    "overtime_allowance",     18, "e"),
    ("Misc Allow",  "misc_allowance",         15, "e"),
    ("Net Pay",     "net_pay",                20, "e"),
]

# Columns for the Bank Transfer Statement (4 columns only)
BANK_TRANSFER_COLUMNS = [
    ("Sr #",          "sr_no",         12, "center"),
    ("Name",          "name",          65, "w"),
    ("Account No.",   "bank_account",  55, "center"),
    ("Amount",        "net_pay",       35, "e"),
]

class ReportsTab:
    def __init__(self, parent):
        self.parent = parent
        self.data = []
        self.month = DEFAULT_MONTH
        self.year = DEFAULT_YEAR
        self.report_type = REPORT_TYPES[0]

        self._build_ui()

    # ----------------------------------------
    # UI
    # ----------------------------------------
    def _build_ui(self):
        top = tk.Frame(self.parent, bg="#f0f4f8")
        top.pack(fill="x", padx=10, pady=15)

        tk.Label(
            top, text="Month:",
            font=("Segoe UI", 10, "bold"), bg="#f0f4f8",
        ).pack(side="left")

        self.month_var = tk.StringVar(value="")
        month_combo = ttk.Combobox(
            top, textvariable=self.month_var,
            values=["Select Month"] + MONTHS, width=15, state="readonly",
        )
        month_combo.current(0)
        month_combo.pack(side="left", padx=5)

        tk.Label(
            top, text="Year:",
            font=("Segoe UI", 10, "bold"), bg="#f0f4f8",
        ).pack(side="left", padx=(15, 5))

        self.year_var = tk.StringVar(value=str(DEFAULT_YEAR))
        tk.Entry(
            top, textvariable=self.year_var,
            font=("Segoe UI", 10), width=8,
        ).pack(side="left")

        tk.Label(
            top, text="Report:",
            font=("Segoe UI", 10, "bold"), bg="#f0f4f8",
        ).pack(side="left", padx=(15, 5))

        self.report_var = tk.StringVar(value=REPORT_TYPES[0])
        ttk.Combobox(
            top, textvariable=self.report_var,
            values=REPORT_TYPES, width=22, state="readonly",
        ).pack(side="left")

        tk.Button(
            top, text="🔄 Load",
            font=("Segoe UI", 10, "bold"),
            bg="#007bff", fg="white",
            padx=15, pady=5, cursor="hand2",
            command=self.load_report,
        ).pack(side="left", padx=15)

        top2 = tk.Frame(self.parent, bg="#f0f4f8")
        top2.pack(fill="x", padx=10, pady=(0, 10))

        tk.Button(
            top2, text="🖨️ Print",
            font=("Segoe UI", 11, "bold"),
            bg="#6c757d", fg="white",
            padx=20, pady=8, cursor="hand2",
            command=self.print_report,
        ).pack(side="left", padx=5)

        tk.Button(
            top2, text="📊 Export Excel",
            font=("Segoe UI", 11, "bold"),
            bg="#28a745", fg="white",
            padx=20, pady=8, cursor="hand2",
            command=self.export_excel,
        ).pack(side="left", padx=5)

        tk.Button(
            top2, text="📄 Export PDF",
            font=("Segoe UI", 11, "bold"),
            bg="#dc3545", fg="white",
            padx=20, pady=8, cursor="hand2",
            command=self.export_pdf,
        ).pack(side="left", padx=5)

        self.info_label = tk.Label(
            self.parent,
            text="Select month and report type, then click 'Load'.",
            font=("Segoe UI", 10, "italic"),
            bg="#f0f4f8", fg="#556677",
        )
        self.info_label.pack(pady=(0, 10))

        tree_frame = tk.Frame(self.parent, bg="#f0f4f8")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = [c[0] for c in REPORT_COLUMNS]
        self.tree = ttk.Treeview(
            tree_frame, columns=cols,
            show="headings", height=18,
        )

        # ---- Professional Styling (Treeview) ----
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#1a3a6b",
            foreground="white",
            relief="flat",
            padding=8
        )
        style.map("Treeview.Heading", background=[("active", "#2a4a7b")])

        style.configure(
            "Treeview",
            font=("Segoe UI", 11),
            rowheight=45,
            background="#ffffff",
            fieldbackground="#ffffff"
        )

        self.tree.tag_configure("oddrow", background="#f8f9fa")
        self.tree.tag_configure("evenrow", background="#ffffff")

        for label, key, width, align in REPORT_COLUMNS:
            self.tree.heading(label, text=label)
            self.tree.column(label, width=int(width * 5), anchor=align, stretch=False)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure(
            "dept_header",
            background="#d4e4f7",
            foreground="#1a3a6b",
            font=("Segoe UI", 11, "bold"),
        )

    def _get_legend_text(self):
        return (
            "Short Forms: "
            "DOJ = Date of Joining | C.T = Class Teacher | Coord = Coordination | "
            "Prev. Pay = Previous Pay | Incr = Increment | GPF = GP Fund | "
            "N. Late = No. of Late Arrivals | LA Ded = Late Arrival Deduction | "
            "N. SL = No. of Short Leaves | SL Ded = Short Leave Deduction | "
            "N. Lv = No. of Leaves | Lv Ded = Leaves Deduction | "
            "N. Abs = No. of Absentees | Abs Ded = Absentee Deduction | "
            "Sec = Security Deduction | Already Ded = Already Deducted Security | "
            "S.Sec = Social Security | Tot Ded = Total Deductions | "
            "OT Hrs/Days = Overtime Hours/Days | OT Allow = Overtime Allowance | "
            "Pay = Payment Mode"
        )

    # ----------------------------------------
    # HELPERS (UPDATED WITH SMART OT LOGIC)
    # ----------------------------------------
    def _fmt_row_value(self, key, val, r):
        if key == "payment_mode":
            mode = (val or "").strip()
            return mode.title() if mode else "—"

        if key == "overtime_display":
            count = r.get("overtime_count") or 0
            ot_type = r.get("overtime_type") or "H"
            rate = r.get("overtime_rate") or 200
            gross = r.get("gross_pay") or 0
            ot_allow = r.get("overtime_allowance") or 0

            # SMART LOGIC: Agar count 0 hai lekin allowance hai, toh calculate karo
            if count == 0 and ot_allow > 0:
                if ot_type == "H" and rate > 0:
                    count = ot_allow / rate
                elif ot_type == "D" and gross > 0:
                    count = ot_allow / (gross / 30)
                else:
                    count = ot_allow / 200 
                    ot_type = "H"

            if count == 0: return "—"
            
            if count == int(count):
                count_str = str(int(count))
            else:
                count_str = f"{count:g}"
                
            return f"{count_str} {ot_type}"

        if key == "overtime_rate_display":
            count = r.get("overtime_count") or 0
            ot_type = r.get("overtime_type") or "H"
            if count == 0: return "—"
            if ot_type == "H":
                rate = r.get("overtime_rate") or 200
                return f"{rate:,.0f}/hr"
            else:
                gross = r.get("gross_pay") or 0
                daily_rate = gross / 30 if gross else 0
                return f"{daily_rate:,.0f}/day"

        if val is None: return ""
        if isinstance(val, (int, float)):
            if key in ("no_late_arrivals", "no_short_leaves", "no_leaves", "no_absentees"):
                return f"{int(val)}"
            if key == "sr_no":
                return f"{int(val)}"
            return f"{val:,.0f}"
        return str(val)

    # ----------------------------------------
    # LOAD
    # ----------------------------------------
    def load_report(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        month = self.month_var.get()
        if not month or month == "Select Month":
            messagebox.showwarning("Month Required", "Please select a month first.")
            return

        try:
            year = int(self.year_var.get())
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.")
            return

        self.month = month
        self.year = year
        self.report_type = self.report_var.get()

        rows = db.get_all_salaries_for_month(month, year)

        if self.report_type == "Cash in Hand":
            rows = [r for r in rows if (r.get("payment_mode") or "").lower() == "cash"]
        elif self.report_type == "Bank Only":
            rows = [r for r in rows if (r.get("payment_mode") or "").lower() == "bank"]
        elif self.report_type == "Bank Transfer Statement":
            rows = [r for r in rows if (r.get("payment_mode") or "").lower() == "bank"]

        rows = [r for r in rows if r.get("net_pay")]
        rows.sort(key=lambda r: int(r.get("sr_no") or 0))

        self.data = rows
        current_dept = None
        total_cols = len(REPORT_COLUMNS)

        row_count = 0
        for r in rows:
            dept = (r.get("department") or "Unassigned").strip() or "Unassigned"

            if dept != current_dept:
                header_vals = [""] * total_cols
                header_vals[0] = f"{dept.upper()} DEPARTMENT"
                self.tree.insert("", "end", values=header_vals, tags=("dept_header",))
                current_dept = dept
                row_count = 0

            row_vals = [self._fmt_row_value(key, r.get(key), r) for (label, key, width, align) in REPORT_COLUMNS]

            tag = "evenrow" if row_count % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=row_vals, tags=(tag,))
            row_count += 1

        total_net = sum((r.get("net_pay") or 0) for r in rows)
        self.info_label.config(
            text=f"{self.report_type} — {month} {year}  |  Staff: {len(rows)}  |  Total Net Pay: Rs. {total_net:,.0f}\n{self._get_legend_text()}"
        )

    # ----------------------------------------
    # PRINT
    # ----------------------------------------
    def print_report(self):
        if not self.data:
            messagebox.showwarning("No Data", "Please load the report first.")
            return
        temp_path = str(get_payslip_dir(self.month, self.year) / f"_report_{self.report_type.replace(' ', '_')}.pdf")
        try:
            self._build_pdf(temp_path)
            os.startfile(temp_path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate PDF:\n{e}")

    # ----------------------------------------
    # EXCEL EXPORT
    # ----------------------------------------
    def export_excel(self):
        if self.report_type == "Bank Transfer Statement":
            return self._export_bank_transfer_excel()

        if not self.data:
            messagebox.showwarning("No Data", "Please load the report first.")
            return

        default_name = f"{self.report_type.replace(' ', '_')}_{self.month}_{self.year}.xlsx"
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=default_name, filetypes=[("Excel files", "*.xlsx")])
        if not path: return

        try:
            import pandas as pd
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
            from openpyxl.drawing.image import Image as OpenpyxlImage

            labels = [c[0] for c in REPORT_COLUMNS]
            excel_data = []

            current_dept = None
            for r in self.data:
                dept = (r.get("department") or "Unassigned").strip() or "Unassigned"
                if dept != current_dept:
                    dept_row = [""] * len(labels)
                    try:
                        name_idx = labels.index("Name")
                        dept_row[name_idx] = f"▼ {dept.upper()}"
                    except ValueError:
                        dept_row[1] = f"▼ {dept.upper()}"
                    excel_data.append(dept_row)
                    current_dept = dept

                row_vals = []
                for (label, key, width, align) in REPORT_COLUMNS:
                    val = self._fmt_row_value_for_excel(key, r.get(key), r)
                    # 0 ki jagah blank
                    if val == 0 or val == "0" or val == "0.0":
                        val = ""
                    row_vals.append(val)
                excel_data.append(row_vals)

            # TOTAL ROW
            total_row = [""] * len(labels)
            try: total_row[labels.index("Name")] = "GRAND TOTAL"
            except ValueError: total_row[1] = "GRAND TOTAL"

            total_basic = round(sum((r.get("basic_pay") or 0) for r in self.data), 2)
            total_gross = round(sum((r.get("gross_pay") or 0) for r in self.data), 2)
            total_ded = round(sum((r.get("total_deductions") or 0) for r in self.data), 2)
            total_ot = round(sum((r.get("overtime_allowance") or 0) for r in self.data), 2)
            total_net = round(sum((r.get("net_pay") or 0) for r in self.data), 2)
            total_misc_ded = round(sum((r.get("misc_deduction") or 0) for r in self.data), 2)
            total_misc_allow = round(sum((r.get("misc_allowance") or 0) for r in self.data), 2)

            for label, val in [("Basic", total_basic), ("Gross", total_gross),
                               ("Misc Ded", total_misc_ded), ("Tot Ded", total_ded),
                               ("OT Allow", total_ot), ("Misc Allow", total_misc_allow),
                               ("Net Pay", total_net)]:
                if label in labels:
                    total_row[labels.index(label)] = val

            excel_data.append(total_row)
            excel_data.append([""] * len(labels))
            excel_data.append([self._get_legend_text()] + [""] * (len(labels) - 1))

            df = pd.DataFrame(excel_data, columns=labels)

            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Report", index=False, startrow=3)
                worksheet = writer.sheets["Report"]

                # LOGO
                try:
                    logo_path = ASSETS_DIR / "school_logo.png"
                    if logo_path.exists():
                        img = OpenpyxlImage(str(logo_path))
                        img.width, img.height = 60, 60
                        worksheet.add_image(img, 'A1')
                except Exception:
                    pass

                # HEADER
                worksheet.merge_cells('B1:H1')
                title_cell = worksheet['B1']
                title_cell.value = SCHOOL_NAME
                title_cell.font = Font(bold=True, size=14, color="1A3A6B")

                worksheet.merge_cells('B2:H2')
                sub_cell = worksheet['B2']
                sub_cell.value = f"{self.report_type} — {self.month} {self.year}"
                sub_cell.font = Font(size=11, color="1A3A6B")

                header_fill = PatternFill("solid", fgColor="1A3A6B")
                header_font = Font(color="FFFFFF", bold=True)

                for col_idx in range(1, len(labels) + 1):
                    cell = worksheet.cell(row=4, column=col_idx)
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

                worksheet.row_dimensions[4].height = 32

                for col_idx, label in enumerate(labels, start=1):
                    max_len = len(label)
                    for row_idx in range(5, len(excel_data) + 5):
                        v = worksheet.cell(row=row_idx, column=col_idx).value
                        if v is not None:
                            max_len = max(max_len, len(str(v)))
                    worksheet.column_dimensions[get_column_letter(col_idx)].width = min(max_len + 2, 22)

            messagebox.showinfo("Success", f"Excel exported:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Excel export failed:\n{e}")

    # ----------------------------------------
    # HELPER FOR EXCEL (UPDATED WITH SMART OT LOGIC)
    # ----------------------------------------
    def _fmt_row_value_for_excel(self, key, val, r):
        if key == "payment_mode":
            mode = (val or "").strip()
            return mode.title() if mode else "—"
            
        if key == "overtime_display":
            count = r.get("overtime_count") or 0
            ot_type = r.get("overtime_type") or "H"
            rate = r.get("overtime_rate") or 200
            gross = r.get("gross_pay") or 0
            ot_allow = r.get("overtime_allowance") or 0

            # SMART LOGIC: Agar count 0 hai lekin allowance hai, toh calculate karo
            if count == 0 and ot_allow > 0:
                if ot_type == "H" and rate > 0:
                    count = ot_allow / rate
                elif ot_type == "D" and gross > 0:
                    count = ot_allow / (gross / 30)
                else:
                    count = ot_allow / 200 
                    ot_type = "H"

            if count == 0: return ""
            
            if count == int(count): 
                count_str = str(int(count))
            else: 
                count_str = f"{count:g}"
                
            return f"{count_str} {ot_type}"
            
        if key == "overtime_rate_display":
            count = r.get("overtime_count") or 0
            ot_type = r.get("overtime_type") or "H"
            if count == 0: return ""
            if ot_type == "H":
                rate = r.get("overtime_rate") or 200
                return f"{rate:,.0f}/hr"
            else:
                gross = r.get("gross_pay") or 0
                daily_rate = round(gross / 30) if gross else 0
                return f"{daily_rate:,.0f}/day"
                
        if val is None: return ""
        if isinstance(val, float):
            if key in ("no_late_arrivals", "no_short_leaves", "no_leaves", "no_absentees"): return int(val)
            return round(val, 2)
        return val

    def _export_bank_transfer_excel(self):
        from src.num2words import amount_in_words
        from src import app_settings
        if not self.data:
            messagebox.showwarning("No Data", "Please load the report first.")
            return
        settings = app_settings.load_settings()
        school_account = settings.get("school_account", "1007862")
        bank_name = settings.get("bank_name", "MCB Satellite Town Branch Sargodha")

        default_name = f"Bank_Transfer_{self.month}_{self.year}.xlsx"
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=default_name, filetypes=[("Excel files", "*.xlsx")])
        if not path: return

        try:
            import pandas as pd
            from openpyxl.styles import Font, PatternFill, Alignment
            total_amount = sum((r.get("net_pay") or 0) for r in self.data)
            total_words = amount_in_words(total_amount)

            rows = []
            rows.append([f"{self.month.upper()}-{self.year}", "", "", ""])
            rows.append(["", "", "", ""])
            rows.append(["From:", "ISLAMIC ALTA VISTA HIGH SCHOOL SARGODHA", "", ""])
            rows.append(["TO:", f"The Manager {bank_name}", "", ""])
            rows.append(["", "", "", ""])
            rows.append(["Respected Sir,", "", "", ""])
            rows.append([f"It is requested that sum of rupees {total_words}/- from our school account # {school_account} may be transferred to the following accounts according to the statement given below:", "", "", ""])
            rows.append(["", "", "", ""])
            rows.append([f"Cheque # ___________________ for {total_words}/- rupees is here by attached.", "", "", ""])
            rows.append(["", "", "", ""])
            rows.append(["Sr #", "Account Holder Name", "Account No.", "Amount (Rs.)"])

            for idx, r in enumerate(self.data, start=1):
                account_holder = r.get("bank_name") or r.get("name", "")
                rows.append([idx, account_holder, r.get("bank_account", "") or "", r.get("net_pay", 0)])

            rows.append(["", "TOTAL", "", total_amount])
            rows.append(["", "", "", ""])
            rows.append(["", "", "", ""])
            rows.append(["Yours sincerely,", "", "", ""])
            rows.append(["", "", "", ""])
            rows.append(["____________________", "", "", ""])
            rows.append(["Principal", "", "", ""])
            rows.append(["Islamic Alta Vista High School", "", "", ""])

            df = pd.DataFrame(rows)
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Bank Transfer", index=False, header=False)
                worksheet = writer.sheets["Bank Transfer"]
                cell = worksheet.cell(row=1, column=1)
                cell.font = Font(bold=True, size=14, color="1A3A6B")
                cell.alignment = Alignment(horizontal="center", vertical="center")
                worksheet.merge_cells("A1:D1")
                for col_idx in range(1, 5):
                    cell = worksheet.cell(row=11, column=col_idx)
                    cell.fill = PatternFill("solid", fgColor="1A3A6B")
                    cell.font = Font(color="FFFFFF", bold=True)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                worksheet.column_dimensions["A"].width = 10
                worksheet.column_dimensions["B"].width = 30
                worksheet.column_dimensions["C"].width = 25
                worksheet.column_dimensions["D"].width = 15
            messagebox.showinfo("Success", f"Excel exported:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Excel export failed:\n{e}")

    # ----------------------------------------
    # PDF EXPORT
    # ----------------------------------------
    def export_pdf(self):
        if not self.data:
            messagebox.showwarning("No Data", "Please load the report first.")
            return
        default_name = f"{self.report_type.replace(' ', '_')}_{self.month}_{self.year}.pdf"
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=default_name, filetypes=[("PDF files", "*.pdf")])
        if not path: return
        try:
            self._build_pdf(path)
            messagebox.showinfo("Success", f"PDF exported:\n{path}")
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Error", f"PDF export failed:\n{e}")

    # ----------------------------------------
    # PDF BUILDER
    # ----------------------------------------
    def _build_pdf(self, path):
        from reportlab.lib.pagesizes import A3, landscape
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

        page_size = landscape(A3)
        if self.report_type == "Bank Transfer Statement":
            return self._build_bank_transfer_pdf(path, page_size)

        doc = SimpleDocTemplate(path, pagesize=page_size, leftMargin=6*mm, rightMargin=6*mm, topMargin=8*mm, bottomMargin=8*mm)
        styles = getSampleStyleSheet()
        story = []

        header_style = ParagraphStyle("H", parent=styles["Title"], fontSize=14, textColor=colors.HexColor("#1a3a6b"), alignment=0, spaceAfter=2)
        sub_style = ParagraphStyle("S", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#1a3a6b"), alignment=0, spaceAfter=0)

        logo_path = ASSETS_DIR / "school_logo.png"
        from reportlab.platypus import Image
        text_block = [Paragraph(SCHOOL_NAME, header_style), Paragraph(f"{self.report_type} — {self.month} {self.year}", sub_style)]

        if logo_path.exists():
            try:
                logo = Image(str(logo_path), width=18*mm, height=18*mm)
                inner_table = Table([[logo, text_block]], colWidths=[22*mm, 95*mm])
                inner_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (0, 0), 0), ("LEFTPADDING", (1, 0), (1, 0), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
                header_table = Table([["", inner_table, ""]], colWidths=[None, 117*mm, None])
                header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "CENTER"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
                story.append(header_table)
            except Exception:
                story.append(Paragraph(SCHOOL_NAME, header_style))
                story.append(Paragraph(f"{self.report_type} — {self.month} {self.year}", sub_style))
        else:
            story.append(Paragraph(SCHOOL_NAME, header_style))
            story.append(Paragraph(f"{self.report_type} — {self.month} {self.year}", sub_style))

        story.append(Spacer(1, 6))

        headers = [c[0] for c in REPORT_COLUMNS]
        table_data = [headers]
        dept_rows = []
        total_cols = len(REPORT_COLUMNS)
        current_dept = None

        for r in self.data:
            dept = (r.get("department") or "Unassigned").strip() or "Unassigned"
            if dept != current_dept:
                header_vals = [""] * total_cols
                header_vals[0] = f"▼ {dept.upper()}"
                table_data.append(header_vals)
                dept_rows.append(len(table_data) - 1)
                current_dept = dept
            row_vals = [self._fmt_row_value(key, r.get(key), r) for (label, key, width, align) in REPORT_COLUMNS]
            table_data.append(row_vals)

        total_basic = sum((r.get("basic_pay") or 0) for r in self.data)
        total_gross = sum((r.get("gross_pay") or 0) for r in self.data)
        total_ded = sum((r.get("total_deductions") or 0) for r in self.data)
        total_ot = sum((r.get("overtime_allowance") or 0) for r in self.data)
        total_net = sum((r.get("net_pay") or 0) for r in self.data)
        total_misc_allow = sum((r.get("misc_allowance") or 0) for r in self.data)
        total_misc_ded = sum((r.get("misc_deduction") or 0) for r in self.data)

        total_row = [""] * total_cols
        total_row[1] = "GRAND TOTAL"
        total_row[3] = f"{total_basic:,.0f}"
        total_row[11] = f"{total_gross:,.0f}"
        total_row[25] = f"{total_misc_ded:,.0f}"
        total_row[26] = f"{total_ded:,.0f}"
        total_row[28] = f"{total_ot:,.0f}"
        total_row[29] = f"{total_misc_allow:,.0f}"
        total_row[30] = f"{total_net:,.0f}"

        table_data.append(total_row)
        total_row_idx = len(table_data) - 1

        col_widths = [c[2] * 2.6 for c in REPORT_COLUMNS]
        page_width_pt = page_size[0] - 12 * mm
        total_width = sum(col_widths)
        if total_width > page_width_pt:
            scale = page_width_pt / total_width
            col_widths = [w * scale for w in col_widths]

        t = Table(table_data, colWidths=col_widths, repeatRows=1)

        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a6b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
            ("FONT", (0, 1), (-1, -1), "Helvetica", 7.5),
            ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#1a3a6b")),
            ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),

            # ---- GRAND TOTAL ROW ----
            ("BACKGROUND", (0, total_row_idx), (-1, total_row_idx), colors.HexColor("#fff3cd")),
            ("FONT", (0, total_row_idx), (-1, total_row_idx), "Helvetica-Bold", 8.5),
            ("TEXTCOLOR", (0, total_row_idx), (-1, total_row_idx), colors.HexColor("#1a3a6b")),
            ("LINEABOVE", (0, total_row_idx), (-1, total_row_idx), 1, colors.HexColor("#1a3a6b")),
        ]

        # Dept header styling
        for idx in dept_rows:
            style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#d4e4f7")))
            style.append(("TEXTCOLOR", (0, idx), (-1, idx), colors.HexColor("#1a3a6b")))
            style.append(("FONT", (0, idx), (-1, idx), "Helvetica-Bold", 8))
            style.append(("SPAN", (0, idx), (-1, idx)))

        t.setStyle(TableStyle(style))
        story.append(t)
        story.append(Spacer(1, 6))

        legend_style = ParagraphStyle("L", parent=styles["Normal"], fontSize=6.5, textColor=colors.grey, alignment=0)
        story.append(Paragraph(self._get_legend_text(), legend_style))

        doc.build(story)

    # ----------------------------------------
    # BANK TRANSFER PDF
    # ----------------------------------------
    def _build_bank_transfer_pdf(self, path, page_size):
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

        from src.num2words import amount_in_words
        from src import app_settings

        settings = app_settings.load_settings()
        school_account = settings.get("school_account", "1007862")
        bank_name = settings.get("bank_name", "MCB Satellite Town Branch Sargodha")

        doc = SimpleDocTemplate(
            path, pagesize=page_size,
            leftMargin=15*mm, rightMargin=15*mm,
            topMargin=12*mm, bottomMargin=12*mm
        )
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle("T", parent=styles["Title"], fontSize=15, textColor=colors.HexColor("#1a3a6b"), alignment=1)
        normal_style = ParagraphStyle("N", parent=styles["Normal"], fontSize=10, leading=14)
        small_style = ParagraphStyle("S", parent=styles["Normal"], fontSize=9, leading=12)

        story.append(Paragraph(SCHOOL_NAME, title_style))
        story.append(Paragraph(f"BANK TRANSFER STATEMENT — {self.month.upper()} {self.year}", ParagraphStyle("sub", parent=styles["Normal"], fontSize=11, textColor=colors.HexColor("#1a3a6b"), alignment=1)))
        story.append(Spacer(1, 10))

        total_amount = sum((r.get("net_pay") or 0) for r in self.data)
        total_words = amount_in_words(total_amount)

        story.append(Paragraph(f"<b>From:</b> ISLAMIC ALTA VISTA HIGH SCHOOL SARGODHA", normal_style))
        story.append(Paragraph(f"<b>To:</b> The Manager {bank_name}", normal_style))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Respected Sir,", normal_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"It is requested that sum of rupees <b>{total_words}/-</b> from our school "
            f"account # {school_account} may be transferred to the following accounts "
            f"according to the statement given below:",
            normal_style
        ))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f"Cheque # ___________________ for <b>{total_words}/-</b> rupees is here by attached.",
            normal_style
        ))
        story.append(Spacer(1, 12))

        table_data = [["Sr #", "Account Holder Name", "Account No.", "Amount (Rs.)"]]
        for idx, r in enumerate(self.data, start=1):
            account_holder = r.get("bank_name") or r.get("name", "")
            table_data.append([
                str(idx),
                str(account_holder),
                str(r.get("bank_account", "") or ""),
                f"{r.get('net_pay', 0):,.0f}",
            ])
        table_data.append(["", "TOTAL", "", f"{total_amount:,.0f}"])

        t = Table(table_data, colWidths=[15*mm, 100*mm, 80*mm, 50*mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a6b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#1a3a6b")),
            ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.lightgrey),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            # TOTAL ROW
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fff3cd")),
            ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 9.5),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#1a3a6b")),
        ]))
        story.append(t)
        story.append(Spacer(1, 25))

        story.append(Paragraph("Yours sincerely,", normal_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph("____________________", normal_style))
        story.append(Paragraph("<b>Principal</b>", normal_style))
        story.append(Paragraph("Islamic Alta Vista High School", small_style))

        doc.build(story)
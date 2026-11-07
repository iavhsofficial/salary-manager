"""
Payslips tab — generate PDF slips for all staff in one click.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox

from src.config import MONTHS, DEFAULT_MONTH, DEFAULT_YEAR, get_payslip_dir
from src import database as db
from src.payslip import generate_payslip


class PayslipTab:
    def __init__(self, parent):
        self.parent = parent
        self._build_ui()

    # ----------------------------------------
    # UI
    # ----------------------------------------
    def _build_ui(self):
        # Top: Month/Year selection
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

        tk.Button(
            top, text="🔄 Preview",
            font=("Segoe UI", 10),
            bg="#007bff", fg="white",
            padx=15, pady=5, cursor="hand2",
            command=self.preview,
        ).pack(side="left", padx=20)

        tk.Button(
            top, text="📄 Generate All Payslips",
            font=("Segoe UI", 11, "bold"),
            bg="#28a745", fg="white",
            padx=20, pady=8, cursor="hand2",
            command=self.generate_all,
        ).pack(side="left", padx=5)

        tk.Button(
            top, text="📂 Open Folder",
            font=("Segoe UI", 10),
            bg="#ffc107", fg="black",
            padx=15, pady=5, cursor="hand2",
            command=self.open_folder,
        ).pack(side="left", padx=5)

        # Info
        self.info_label = tk.Label(
            self.parent,
            text="Select a month, then click 'Generate All Payslips'.",
            font=("Segoe UI", 10, "italic"),
            bg="#f0f4f8", fg="#556677",
        )
        self.info_label.pack(pady=(0, 10))

        # Preview table
        tree_frame = tk.Frame(self.parent, bg="#f0f4f8")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = (
            "Sr", "Name", "Net Pay", "Payslip Status"
        )
        self.tree = ttk.Treeview(
            tree_frame, columns=columns,
            show="headings", height=18,
        )

        widths = [50, 250, 120, 200]
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    # ----------------------------------------
    # PREVIEW
    # ----------------------------------------
    def preview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        month = self.month_var.get()
        try:
            year = int(self.year_var.get())
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.")
            return

        rows = db.get_all_salaries_for_month(month, year)
        folder = get_payslip_dir(month, year)

        ready = 0
        pending = 0
        no_salary = 0

        for s in rows:
            name = s.get("name", "")
            net = s.get("net_pay") or 0

            # Check if salary was entered
            has_salary = bool(net)

            # Check if PDF already exists
            safe_name = name.replace(" ", "_")
            pdf_path = folder / f"{safe_name}.pdf"
            has_pdf = pdf_path.exists()

            if has_pdf:
                status = "✅ Ready"
                ready += 1
            elif has_salary:
                status = "⏳ Not generated"
                pending += 1
            else:
                status = "⚠ No salary entered"
                no_salary += 1

            self.tree.insert("", "end", iid=str(s["staff_id"]), values=(
                s.get("sr_no", ""),
                name,
                f"{net:,.0f}" if net else "—",
                status,
            ))

        self.info_label.config(
            text=f"{month} {year} — "
                 f"Ready: {ready}  |  Pending: {pending}  |  "
                 f"No salary: {no_salary}  |  Total: {len(rows)}"
        )

    # ----------------------------------------
    # GENERATE ALL
    # ----------------------------------------
    def generate_all(self):
        month = self.month_var.get()
        if not month or month == "Select Month":
            messagebox.showwarning("Month Required", "Please select a month first.")
            return
        
        try:
            year = int(self.year_var.get())
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.")
            return
        
        rows = db.get_all_salaries_for_month(month, year)

        # Filter only those with salary entered
        ready_rows = [r for r in rows if r.get("net_pay")]

        if not ready_rows:
            messagebox.showwarning(
                "No Data",
                f"No salary records found for {month} {year}.\n\n"
                "Please enter salaries in the 'Salary Entry' tab first."
            )
            return

        confirm = messagebox.askyesno(
            "Generate Payslips",
            f"Generate payslips for {len(ready_rows)} staff members?\n\n"
            f"Month: {month} {year}\n"
            f"Folder: payslips/{month}_{year}/"
        )
        if not confirm:
            return

        success = 0
        failed = 0

        for s in ready_rows:
            try:
                staff_dict = {
                    "name": s.get("name", ""),
                    "sr_no": s.get("sr_no", ""),
                    "date_of_joining": s.get("date_of_joining", ""),
                    "basic_pay": s.get("basic_pay", 0),
                    "department": s.get("department", ""),
                    "designation": s.get("designation", ""),
                    "payment_mode": s.get("payment_mode", "Cash"),
                }

                salary_dict = {
                    "writing": s.get("writing", 0),
                    "speaking": s.get("speaking", 0),
                    "checking": s.get("checking", 0),
                    "class_teacher": s.get("class_teacher", 0),
                    "coordination": s.get("coordination", 0),
                    "previous_pay": s.get("previous_pay", 0),
                    "increment": s.get("increment", 0),
                    "overtime_allowance": s.get("overtime_allowance", 0),
                    "gross_pay": s.get("gross_pay", 0),
                    "no_late_arrivals": s.get("no_late_arrivals", 0),
                    "late_arrival_deduction": s.get("late_arrival_deduction", 0),
                    "no_short_leaves": s.get("no_short_leaves", 0),
                    "short_leave_deduction": s.get("short_leave_deduction", 0),
                    "no_leaves": s.get("no_leaves", 0),
                    "leaves_deduction": s.get("leaves_deduction", 0),
                    "absentee_deduction": s.get("absentee_deduction", 0),
                    "gp_fund": s.get("gp_fund", 0),
                    "social_security": s.get("social_security", 0),
                    "security_deduction": s.get("security_deduction", 0),
                    "oab": s.get("oab", 0),
                    "total_deductions": s.get("total_deductions", 0),
                    "net_pay": s.get("net_pay", 0),
                }

                generate_payslip(staff_dict, salary_dict, month, year)
                success += 1

            except Exception as e:
                print(f"Error for {s.get('name')}: {e}")
                failed += 1

        messagebox.showinfo(
            "Payslips Generated",
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n\n"
            f"Folder: payslips/{month}_{year}/"
        )
        self.preview()

    # ----------------------------------------
    # OPEN FOLDER
    # ----------------------------------------
    def open_folder(self):
        month = self.month_var.get()
        if not month or month == "Select Month":
            messagebox.showwarning("Month Required", "Please select a month first.")
            return

        try:
            year = int(self.year_var.get())
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.")
            return

        folder = get_payslip_dir(month, year)

        # Windows: use explorer
        try:
            os.startfile(str(folder))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")
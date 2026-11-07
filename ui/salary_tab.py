"""
Salary Entry tab — monthly salary entry with auto-calculation.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from src.config import MONTHS, DEFAULT_MONTH, DEFAULT_YEAR
from src import database as db
from src.calculations import calculate_salary


class SalaryTab:
    def __init__(self, parent):
        self.parent = parent
        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self.parent, bg="#f0f4f8")
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="Month:", font=("Segoe UI", 10, "bold"),
                 bg="#f0f4f8").pack(side="left")

        self.month_var = tk.StringVar(value="")
        month_combo = ttk.Combobox(
            top, textvariable=self.month_var,
            values=["Select Month"] + MONTHS, width=15, state="readonly",
        )
        month_combo.current(0)
        month_combo.pack(side="left", padx=5)

        tk.Label(top, text="Year:", font=("Segoe UI", 10, "bold"),
                 bg="#f0f4f8").pack(side="left", padx=(15, 5))

        self.year_var = tk.StringVar(value=str(DEFAULT_YEAR))
        tk.Entry(top, textvariable=self.year_var,
                 font=("Segoe UI", 10), width=8).pack(side="left")

        tk.Button(top, text="🔄 Load Staff", font=("Segoe UI", 10, "bold"),
                  bg="#007bff", fg="white", padx=15, pady=5, cursor="hand2",
                  command=self.load_staff).pack(side="left", padx=20)

        # Naya Button Copy Last Month
        tk.Button(top, text="📋 Copy Last Month", font=("Segoe UI", 10, "bold"),
                  bg="#ffc107", fg="black", padx=15, pady=5, cursor="hand2",
                  command=self.copy_last_month).pack(side="left", padx=5)

        # Naya Button: Clear This Month
        tk.Button(top, text="🗑️ Clear This Month", font=("Segoe UI", 10, "bold"),
                  bg="#dc3545", fg="white", padx=15, pady=5, cursor="hand2",
                  command=self.clear_month_data).pack(side="left", padx=5)

        self.info_label = tk.Label(
            self.parent,
            text="Select a month and click 'Load Staff'.",
            font=("Segoe UI", 10, "italic"), bg="#f0f4f8", fg="#556677",
        )
        self.info_label.pack(pady=(0, 10))

        tree_frame = tk.Frame(self.parent, bg="#f0f4f8")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("Sr", "Name", "Basic Pay", "Gross Pay", "Total Ded", "Net Pay")
        self.tree = ttk.Treeview(tree_frame, columns=columns,
                                 show="headings", height=18)

        widths = [50, 220, 100, 120, 120, 120]
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.edit_salary)

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            self.tree.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(event):
            self.tree.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(event):
            self.tree.unbind_all("<MouseWheel>")

        self.tree.bind("<Enter>", _bind_wheel)
        self.tree.bind("<Leave>", _unbind_wheel)
        
    def load_staff(self):
        month = self.month_var.get()
        if not month or month == "Select Month":
            messagebox.showwarning("Month Required", "Please select a month first.")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            year = int(self.year_var.get())
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.")
            return

        rows = db.get_all_salaries_for_month(month, year)

        for s in rows:
            gross = s.get("gross_pay") or 0
            ded = s.get("total_deductions") or 0
            net = s.get("net_pay") or 0

            self.tree.insert("", "end", iid=str(s["staff_id"]), values=(
                s.get("sr_no", ""),
                s.get("name", ""),
                f"{s.get('basic_pay', 0):,.0f}",
                f"{gross:,.0f}" if gross else "—",
                f"{ded:,.0f}" if ded else "—",
                f"{net:,.0f}" if net else "—",
            ))

        self.info_label.config(
            text=f"{len(rows)} staff loaded for {month} {year} — Double-click any row to enter salary"
        )

    def copy_last_month(self):
        month = self.month_var.get()
        if not month or month == "Select Month":
            messagebox.showwarning("Month Required", "Please select a month first.")
            return

        try:
            year = int(self.year_var.get())
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.")
            return

        existing_data = db.get_all_salaries_for_month(month, year)
        already_saved = any(r.get("net_pay") for r in existing_data)
        
        if already_saved:
            confirm = messagebox.askyesno(
                "Data Already Exists", 
                f"{month} {year} ki salary pehle se save hai.\n\n"
                "Kya aap dobara copy karna chahti hain? (Purana data overwrite ho jayega)"
            )
            if not confirm: return

        month_order = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        current_idx = month_order.index(month)
        if current_idx == 0:
            prev_month = "December"
            prev_year = year - 1
        else:
            prev_month = month_order[current_idx - 1]
            prev_year = year

        prev_data = db.get_all_salaries_for_month(prev_month, prev_year)
        if not prev_data:
            messagebox.showerror("Error", f"{prev_month} {prev_year} ka data nahi mila.")
            return

        copied_count = 0
        for row in prev_data:
            if not row.get("net_pay"): continue

            staff_id = row["staff_id"]
            
            # Security Auto-Deduct Logic
            has_security_plan = float(row.get("security_total") or 0) > 0
            per_month_sec = float(row.get("security_per_month") or 0)
            
            new_data = {
                "writing": row.get("writing", 0),
                "speaking": row.get("speaking", 0),
                "checking": row.get("checking", 0),
                "class_teacher": row.get("class_teacher", 0),
                "coordination": row.get("coordination", 0),
                "gp_fund": row.get("gp_fund", 0),
                "previous_pay": 0, "increment": 0,
                "ot_hours": 0, "ot_days": 0, "overtime_allowance": 0,
                "no_late_arrivals": 0, "late_arrival_deduction": 0,
                "no_short_leaves": 0, "short_leave_deduction": 0,
                "no_leaves": 0, "leaves_deduction": 0,
                "no_absentees": 0, "absentee_deduction": 0,
                
                # Security Khud-ba-khud deduct hogi agar plan mojood hai
                "security_deduction": per_month_sec if has_security_plan else 0, 
                "apply_security": 1 if has_security_plan else 0,
                
                "apply_social_security": row.get("apply_social_security", 0),
                "apply_oab": row.get("apply_oab", 0),
            }

            result = calculate_salary(row["basic_pay"], new_data)
            db.save_salary(staff_id, month, year, result)
            copied_count += 1

        self.load_staff()
        messagebox.showinfo("Success", f"{copied_count} staff members ki salary {prev_month} se {month} mein copy ho gayi.")

    def clear_month_data(self):
        """Delete all salary records for the selected month."""
        month = self.month_var.get()
        if not month or month == "Select Month":
            messagebox.showwarning("Month Required", "Please select a month first.")
            return

        try:
            year = int(self.year_var.get())
        except ValueError:
            messagebox.showerror("Error", "Year must be a number.")
            return

        confirm = messagebox.askyesno(
            "Clear Month Data", 
            f"Kya aap waqai {month} {year} ki saari salary delete karna chahti hain?\n\n"
            "Yeh action undo nahi ho sakta (Staff ki details safe rahengi, sirf is mahine ki salary delete hogi)."
        )
        if not confirm:
            return

        from src.database import get_connection
        try:
            with get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM salary WHERE month=? AND year=?", (month, year))
            
            self.load_staff()
            messagebox.showinfo("Success", f"{month} {year} ka saara data delete ho gaya hai.")
        except Exception as e:
            messagebox.showerror("Error", f"Data delete nahi ho saka:\n{e}")

    def edit_salary(self, event):
        selection = self.tree.selection()
        if not selection: return

        staff_id = int(selection[0])
        staff = db.get_staff(staff_id)
        if not staff:
            messagebox.showerror("Error", "Staff not found.")
            return

        SalaryDialog(self.parent, staff, month=self.month_var.get(),
                     year=int(self.year_var.get()), on_save=self.load_staff)


class SalaryDialog:
    def __init__(self, parent, staff, month, year, on_save=None):
        self.staff = staff
        self.month = month
        self.year = year
        self.on_save = on_save

        self.existing = db.get_salary(staff["id"], month, year) or {}
        self._recalculating = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Salary Entry — {staff['name']}")
        self.dialog.configure(bg="#f0f4f8")

        w, h = 720, 750
        self.dialog.update_idletasks()
        sw, sh = self.dialog.winfo_screenwidth(), self.dialog.winfo_screenheight()
        self.dialog.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2-30}")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._build()
        self._populate()

    def _build(self):
        header = tk.Frame(self.dialog, bg="#1a3a6b", height=70)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text=f"{self.staff['name']} — {self.month} {self.year}",
                 font=("Segoe UI", 13, "bold"), bg="#1a3a6b", fg="white").pack(pady=(12, 0))
        tk.Label(header, text=f"Basic Pay: Rs. {self.staff.get('basic_pay', 0):,.0f}",
                 font=("Segoe UI", 10), bg="#1a3a6b", fg="#c9d6e8").pack()

        btn_frame = tk.Frame(self.dialog, bg="#f0f4f8", height=60)
        btn_frame.pack(side="bottom", fill="x"); btn_frame.pack_propagate(False)
        tk.Button(btn_frame, text="💾 Save Salary", font=("Segoe UI", 11, "bold"),
                  bg="#28a745", fg="white", padx=25, pady=10, cursor="hand2",
                  command=self.save).pack(side="left", padx=15, pady=10)
        tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 11),
                  bg="#6c757d", fg="white", padx=25, pady=10, cursor="hand2",
                  command=self.dialog.destroy).pack(side="left", padx=5, pady=10)

        container = tk.Frame(self.dialog, bg="#f0f4f8")
        container.pack(fill="both", expand=True, padx=15, pady=10)
        canvas = tk.Canvas(container, bg="#f0f4f8", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        form = tk.Frame(canvas, bg="#f0f4f8")
        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")

        self.entries = {}
        row = 0

        def section(title):
            nonlocal row
            tk.Label(form, text=title, font=("Segoe UI", 11, "bold"),
                     bg="#f0f4f8", fg="#1a3a6b", anchor="w").grid(row=row, column=0, columnspan=3, sticky="w", pady=(12, 4), padx=5)
            row += 1

        def field(label, key, width=15):
            nonlocal row
            tk.Label(form, text=label, font=("Segoe UI", 10), bg="#f0f4f8", anchor="w").grid(row=row, column=0, sticky="w", pady=3, padx=5)
            e = tk.Entry(form, font=("Segoe UI", 10), width=width)
            e.grid(row=row, column=1, sticky="w", pady=3)
            e.bind("<KeyRelease>", lambda ev: self.recalculate())
            self.entries[key] = e
            row += 1

        # EARNINGS
        section("— EARNINGS —")
        
        tk.Label(form, text="Basic Pay", font=("Segoe UI", 10), bg="#f0f4f8", anchor="w").grid(row=row, column=0, sticky="w", pady=3, padx=5)
        self.basic_pay_entry = tk.Entry(form, font=("Segoe UI", 10), width=15)
        self.basic_pay_entry.insert(0, str(self.staff.get("basic_pay", 0)))
        self.basic_pay_entry.grid(row=row, column=1, sticky="w", pady=3)
        self.basic_pay_entry.bind("<KeyRelease>", lambda ev: self.recalculate())
        self.entries["basic_pay"] = self.basic_pay_entry
        row += 1

        field("Writing", "writing")
        field("Speaking", "speaking")
        field("Checking", "checking")
        field("Class Teacher (C.T)", "class_teacher")
        field("Coordination", "coordination")
        field("Previous Pay (reference only)", "previous_pay")
        field("Increment", "increment")
        field("Misc Allowance (Rs.)", "misc_allowance")  # NAYA

        # OVERTIME
        section("— OVERTIME (Hours & Days) —")
        field("Overtime Hours", "ot_hours")
        field("Overtime Days", "ot_days")
        
        tk.Label(form, text="Overtime Allowance (Rs.)", font=("Segoe UI", 10), bg="#f0f4f8", anchor="w").grid(row=row, column=0, sticky="w", pady=3, padx=5)
        self.overtime_amount_entry = tk.Entry(form, font=("Segoe UI", 10), width=15, state="readonly")
        self.overtime_amount_entry.grid(row=row, column=1, sticky="w", pady=3)
        self.entries["overtime_allowance"] = self.overtime_amount_entry
        row += 1

        # LEAVES
        section("— LEAVES & ABSENTEES —")
        field("No. of Late Arrivals", "no_late_arrivals")
        field("No. of Short Leaves", "no_short_leaves")
        field("No. of Full Leaves", "no_leaves")
        field("No. of Absentees", "no_absentees")

        # DEDUCTIONS
        section("— DEDUCTIONS —")
        self.apply_ss_var = tk.BooleanVar(value=False)
        tk.Checkbutton(form, text="Apply Social Security", variable=self.apply_ss_var,
                       font=("Segoe UI", 10, "bold"), bg="#f0f4f8", command=self.recalculate).grid(row=row, column=0, sticky="w", pady=3, padx=5)
        tk.Label(form, text="(Auto from Settings)", font=("Segoe UI", 9), bg="#f0f4f8", fg="#556677").grid(row=row, column=1, sticky="w")
        row += 1

        self.apply_oab_var = tk.BooleanVar(value=False)
        tk.Checkbutton(form, text="Apply OAB", variable=self.apply_oab_var,
                       font=("Segoe UI", 10, "bold"), bg="#f0f4f8", command=self.recalculate).grid(row=row, column=0, sticky="w", pady=3, padx=5)
        tk.Label(form, text="(Auto from Settings)", font=("Segoe UI", 9), bg="#f0f4f8", fg="#556677").grid(row=row, column=1, sticky="w")
        row += 1
        
        field("Misc Deduction (Rs.)", "misc_deduction")  # NAYA

        # SECURITY
        section("— SECURITY DEDUCTION (Refundable) —")
        sec_frame = tk.Frame(form, bg="#f0f4f8")
        sec_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=5, padx=5)
        row += 1

        self.apply_security_var = tk.BooleanVar(value=False)
        self.security_checkbox = tk.Checkbutton(sec_frame, text="Apply Security Deduction This Month",
            variable=self.apply_security_var, font=("Segoe UI", 10, "bold"), bg="#f0f4f8", fg="#1a3a6b",
            activebackground="#f0f4f8", command=self._toggle_security_fields)
        self.security_checkbox.pack(side="left")

        self.security_info_label = tk.Label(form, text="", font=("Segoe UI", 9), bg="#f0f4f8", fg="#556677", justify="left", anchor="w")
        self.security_info_label.grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 5))
        row += 1

        self.security_amount_label = tk.Label(form, text="This Month Security Deduction:", font=("Segoe UI", 10, "bold"), bg="#f0f4f8", anchor="w")
        self.security_amount_entry = tk.Entry(form, font=("Segoe UI", 10), width=15)
        self.security_amount_entry.bind("<KeyRelease>", lambda ev: self.recalculate())
        self.entries["security_deduction"] = self.security_amount_entry
        self._security_amount_row = row
        row += 1

        # TOTALS
        section("— CALCULATED TOTALS —")
        self.gross_var = tk.StringVar(value="0"); self.total_earn_var = tk.StringVar(value="0")
        self.total_ded_var = tk.StringVar(value="0"); self.net_pay_var = tk.StringVar(value="0")
        self.gp_fund_var = tk.StringVar(value="200"); self.late_ded_var = tk.StringVar(value="0")
        self.short_ded_var = tk.StringVar(value="0"); self.leave_ded_var = tk.StringVar(value="0")
        self.absentee_ded_var = tk.StringVar(value="0"); self.social_sec_var = tk.StringVar(value="0")
        self.oab_var = tk.StringVar(value="0")
        
        # Naye Variables
        self.misc_allow_var = tk.StringVar(value="0")
        self.misc_ded_var = tk.StringVar(value="0")
        self.security_ded_var = tk.StringVar(value="0")

        for label, var in [
            ("GP Fund (fixed)", self.gp_fund_var), 
            ("Late Arrival Deduction", self.late_ded_var),
            ("Short Leave Deduction", self.short_ded_var), 
            ("Leaves Deduction", self.leave_ded_var),
            ("Absentee Deduction", self.absentee_ded_var), 
            ("Security Deduction", self.security_ded_var), # NAYA
            ("Social Security", self.social_sec_var),
            ("OAB", self.oab_var), 
            ("Misc Deduction", self.misc_ded_var), # NAYA
            ("Gross Pay (without OT)", self.gross_var),
            ("Misc Allowance", self.misc_allow_var), # NAYA
            ("Total Earnings (with OT)", self.total_earn_var), 
            ("Total Deductions", self.total_ded_var),
            ("NET PAY", self.net_pay_var),
        ]:
            tk.Label(form, text=label, font=("Segoe UI", 10, "bold"), bg="#f0f4f8", fg="#1a3a6b", anchor="w").grid(row=row, column=0, sticky="w", pady=3, padx=5)
            tk.Label(form, textvariable=var, font=("Segoe UI", 10, "bold"), bg="#f0f4f8", fg="#28a745", anchor="w").grid(row=row, column=1, sticky="w", pady=3)
            row += 1

    def _num(self, key):
        try:
            v = self.entries[key].get().strip()
            return float(v) if v else 0
        except: return 0

    def _update_security_info(self):
        total = float(self.staff.get("security_total") or 0)
        installments = int(self.staff.get("security_installments") or 0)
        per_month = float(self.staff.get("security_per_month") or 0)
        already = float(self.staff.get("security_already_deducted") or 0)
        remaining = total - already
        if total <= 0:
            self.security_checkbox.config(state="disabled")
            self.security_info_label.config(text="⚠ No security plan set for this staff.\nSet Total Security in the Staff form first.", fg="#dc3545")
        else:
            self.security_checkbox.config(state="normal")
            self.security_info_label.config(text=f"Total Security: Rs. {total:,.0f}    |    Installments: {installments}    |    Per Month: Rs. {per_month:,.0f}\nAlready Deducted: Rs. {already:,.0f}    |    Remaining: Rs. {remaining:,.0f}", fg="#556677")

    def _toggle_security_fields(self):
        if self.apply_security_var.get():
            total = float(self.staff.get("security_total") or 0)
            already = float(self.staff.get("security_already_deducted") or 0)
            remaining = total - already
            if remaining <= 0:
                messagebox.showwarning("Security Complete", f"Security already fully deducted.")
            self.security_amount_label.grid(row=self._security_amount_row, column=0, sticky="w", pady=3, padx=5)
            self.security_amount_entry.grid(row=self._security_amount_row, column=1, sticky="w", pady=3)
            current = self.security_amount_entry.get().strip()
            if not current or current == "0":
                per_month = float(self.staff.get("security_per_month") or 0)
                if per_month > 0:
                    suggested = min(per_month, remaining) if remaining > 0 else per_month
                    self.security_amount_entry.delete(0, tk.END)
                    self.security_amount_entry.insert(0, f"{suggested:.0f}")
        else:
            self.security_amount_label.grid_remove()
            self.security_amount_entry.grid_remove()
            self.security_amount_entry.delete(0, tk.END)
            self.security_amount_entry.insert(0, "0")
        if not self._recalculating: self.recalculate()

    def _populate(self):
        source = self.existing or db.get_previous_salary(self.staff["id"], self.month, self.year) or {}
        auto_keys = ["writing", "speaking", "checking", "class_teacher", "coordination"]
        existing_only = ["previous_pay", "increment", "ot_hours", "ot_days", "no_late_arrivals", "no_short_leaves", "no_leaves", "no_absentees", "misc_allowance", "misc_deduction"]
        
        for key in auto_keys:
            val = source.get(key, 0) or 0
            self.entries[key].delete(0, tk.END); self.entries[key].insert(0, str(int(val) if val==int(val) else val))

        for key in existing_only:
            val = self.existing.get(key, 0) or 0 if self.existing else 0
            self.entries[key].delete(0, tk.END); self.entries[key].insert(0, str(int(val) if val==int(val) else val))

        # Basic Pay Load
        self.entries["basic_pay"].delete(0, tk.END)
        self.entries["basic_pay"].insert(0, str(self.staff.get("basic_pay", 0)))

        # Check karein ke staff ka security plan set hai ya nahi
        has_security_plan = float(self.staff.get("security_total") or 0) > 0

        # Security Checkbox Auto-Fill Logic
        if self.existing:
            # Agar pehle se save hai, toh wohi state load karein
            self.apply_security_var.set(bool(self.existing.get("apply_security", 0)))
            sec_val = self.existing.get("security_deduction", 0) or 0
            self.security_amount_entry.delete(0, tk.END)
            if sec_val: self.security_amount_entry.insert(0, f"{sec_val:.0f}")
            
            self.apply_ss_var.set(bool(self.existing.get("apply_social_security", 0)))
            self.apply_oab_var.set(bool(self.existing.get("apply_oab", 0)))
        else:
            # Agar naya record hai:
            # Agar plan mojood hai toh auto-tick (True), warna uncheck (False)
            self.apply_security_var.set(has_security_plan)
            
            self.security_amount_entry.delete(0, tk.END)
            if has_security_plan:
                # Khud-ba-khud 'Per Month' wali amount daal dein
                per_month = float(self.staff.get("security_per_month") or 0)
                if per_month > 0:
                    self.security_amount_entry.insert(0, f"{per_month:.0f}")

            self.apply_ss_var.set(False)
            self.apply_oab_var.set(False)

        self._update_security_info()
        self._toggle_security_fields()
        self.recalculate()

    def recalculate(self):
        if getattr(self, "_recalculating", False): return
        self._recalculating = True
        try:
            basic_pay = self._num("basic_pay") or self.staff.get("basic_pay", 0)
            inputs = {
                "writing": self._num("writing"), "speaking": self._num("speaking"), "checking": self._num("checking"),
                "class_teacher": self._num("class_teacher"), "coordination": self._num("coordination"),
                "previous_pay": self._num("previous_pay"), "increment": self._num("increment"),
                "ot_hours": self._num("ot_hours"), "ot_days": self._num("ot_days"),
                "no_late_arrivals": int(self._num("no_late_arrivals")), "no_short_leaves": int(self._num("no_short_leaves")),
                "no_leaves": int(self._num("no_leaves")), "no_absentees": int(self._num("no_absentees")),
                "apply_social_security": 1 if self.apply_ss_var.get() else 0, "apply_oab": 1 if self.apply_oab_var.get() else 0,
                "security_deduction": (self._num("security_deduction") if self.apply_security_var.get() else 0),
                "apply_security": 1 if self.apply_security_var.get() else 0,
                "misc_allowance": self._num("misc_allowance"),
                "misc_deduction": self._num("misc_deduction"),
            }
            result = calculate_salary(basic_pay, inputs)

            self.gp_fund_var.set(f"{result['gp_fund']:,.0f}")
            self.late_ded_var.set(f"{result['late_arrival_deduction']:,.0f}")
            self.short_ded_var.set(f"{result['short_leave_deduction']:,.0f}")
            self.leave_ded_var.set(f"{result['leaves_deduction']:,.0f}")
            self.absentee_ded_var.set(f"{result.get('absentee_deduction', 0):,.0f}")
            self.social_sec_var.set(f"{result.get('social_security', 0):,.0f}")
            self.oab_var.set(f"{result.get('oab', 0):,.0f}")
            
            # Naye values set karein
            self.security_ded_var.set(f"{result.get('security_deduction', 0):,.0f}")
            self.misc_allow_var.set(f"{result.get('misc_allowance', 0):,.0f}")
            self.misc_ded_var.set(f"{result.get('misc_deduction', 0):,.0f}")

            self.gross_var.set(f"Rs. {result['gross_pay']:,.0f}")
            self.total_earn_var.set(f"Rs. {result['total_earnings']:,.0f}")
            self.total_ded_var.set(f"Rs. {result['total_deductions']:,.0f}")
            self.net_pay_var.set(f"Rs. {result['net_pay']:,.0f}")

            self._last_result = result

            ot_amount = result.get("overtime_allowance", 0) or 0
            self.overtime_amount_entry.config(state="normal")
            self.overtime_amount_entry.delete(0, tk.END)
            self.overtime_amount_entry.insert(0, f"{ot_amount:,.0f}")
            self.overtime_amount_entry.config(state="readonly")
        finally:
            self._recalculating = False

    def save(self):
        self.recalculate()
        result = self._last_result

        # Basic Pay update karein staff table mein
        new_basic_pay = self._num("basic_pay")
        if new_basic_pay and new_basic_pay != self.staff.get("basic_pay", 0):
            db.update_staff(self.staff["id"], basic_pay=new_basic_pay)

        old_security = float(self.existing.get("security_deduction") or 0)
        new_security = float(result.get("security_deduction") or 0)
        adjustment = new_security - old_security

        db.save_salary(self.staff["id"], self.month, self.year, result)

        if adjustment != 0:
            db.update_security_deducted(self.staff["id"], adjustment)

        messagebox.showinfo("Saved", f"Salary saved.\nNet Pay: Rs. {result['net_pay']:,.0f}")
        self.dialog.destroy()
        if self.on_save: self.on_save()
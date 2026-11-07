"""
Staff management tab — add, edit, delete staff members.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from src import database as db


class StaffTab:
    def __init__(self, parent):
        self.parent = parent
        self._build_ui()
        self.refresh()

    # ----------------------------------------
    # UI BUILD
    # ----------------------------------------
    def _build_ui(self):
        # Top toolbar
        top = tk.Frame(self.parent, bg="#f0f4f8")
        top.pack(fill="x", padx=10, pady=10)

        tk.Button(
            top, text="➕ Add New Staff",
            font=("Segoe UI", 10, "bold"),
            bg="#28a745", fg="white",
            padx=15, pady=8, cursor="hand2",
            command=self.open_add_dialog,
        ).pack(side="left")

        tk.Button(
            top, text="✏️ Edit Selected",
            font=("Segoe UI", 10),
            bg="#ffc107", fg="black",
            padx=15, pady=8, cursor="hand2",
            command=self.open_edit_dialog,
        ).pack(side="left", padx=5)

        tk.Button(
            top, text="🗑️ Delete Selected",
            font=("Segoe UI", 10),
            bg="#dc3545", fg="white",
            padx=15, pady=8, cursor="hand2",
            command=self.delete_selected,
        ).pack(side="left", padx=5)

        tk.Button(
            top, text="🔄 Refresh",
            font=("Segoe UI", 10),
            bg="#007bff", fg="white",
            padx=15, pady=8, cursor="hand2",
            command=self.refresh,
        ).pack(side="left", padx=5)
        
        tk.Button(
            top, text="💾 Backup DB",
            font=("Segoe UI", 10, "bold"),
            bg="#6f42c1", fg="white",
            padx=15, pady=8, cursor="hand2",
            command=self.backup_database,
        ).pack(side="left", padx=5)

        tk.Button(
            top, text="📥 Import Excel",
            font=("Segoe UI", 10, "bold"),
            bg="#17a2b8", fg="white",
            padx=15, pady=8, cursor="hand2",
            command=self.import_from_excel,
        ).pack(side="left", padx=5)
        
        # Search box
        tk.Label(
            top, text="Search:", font=("Segoe UI", 10),
            bg="#f0f4f8",
        ).pack(side="left", padx=(20, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh())

        tk.Entry(
            top, textvariable=self.search_var,
            font=("Segoe UI", 10), width=20,
        ).pack(side="left")

        # Department Filter
        tk.Label(
            top, text="Dept:", font=("Segoe UI", 10),
            bg="#f0f4f8",
        ).pack(side="left", padx=(15, 5))

        self.dept_var = tk.StringVar(value="All")
        default_depts = ["All", "PHOENIX", "ADMIN"]
        
        self.dept_combo = ttk.Combobox(
            top, textvariable=self.dept_var,
            values=default_depts, width=15, state="readonly",
        )
        self.dept_combo.pack(side="left")
        self.dept_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Sort By Dropdown
        tk.Label(
            top, text="Sort By:", font=("Segoe UI", 10),
            bg="#f0f4f8",
        ).pack(side="left", padx=(15, 5))

        self.sort_var = tk.StringVar(value="Serial No")
        self.sort_combo = ttk.Combobox(
            top, textvariable=self.sort_var,
            values=["Serial No", "Department", "Date of Joining"], 
            width=15, state="readonly",
        )
        self.sort_combo.pack(side="left")
        self.sort_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        
        # Treeview with scrollbar
        tree_frame = tk.Frame(self.parent, bg="#f0f4f8")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = (
            "ID", "Sr", "Name", "DOJ", "Department",
            "Designation", "Gross Pay", "Payment Mode", "WhatsApp"
        )
        self.tree = ttk.Treeview(
            tree_frame, columns=columns,
            show="headings", height=20,
        )

        widths = [50, 50, 220, 110, 140, 140, 120, 130, 140]
        
        for col, w in zip(columns, widths):
            self.tree.heading(col, text=col, anchor="center")
            if col in ("ID", "Sr", "DOJ", "Gross Pay", "Payment Mode"):
                self.tree.column(col, width=w, anchor="center")
            else:
                self.tree.column(col, width=w, anchor="w")

        # ---- Professional Styling ----
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#1a3a6b",
            foreground="white",
            relief="flat",
            padding=8
        )
        style.map("Treeview.Heading", background=[("active", "#2a4a7b")])
        
        style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=35,
            background="#ffffff",
            fieldbackground="#ffffff"
        )
        
        self.tree.tag_configure("oddrow", background="#f8f9fa")
        self.tree.tag_configure("evenrow", background="#ffffff")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", lambda e: self.open_edit_dialog())

        self.counter_label = tk.Label(
            self.parent, text="0 staff members",
            font=("Segoe UI", 9, "italic"),
            bg="#f0f4f8", fg="#556677", anchor="w",
        )
        self.counter_label.pack(fill="x", padx=15, pady=(0, 10))

    # ----------------------------------------
    # REFRESH LIST
    # ----------------------------------------
    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        search = self.search_var.get().strip() if hasattr(self, "search_var") else ""
        dept = self.dept_var.get() if hasattr(self, "dept_var") else "All"
        
        sort_selection = self.sort_var.get() if hasattr(self, "sort_var") else "Serial No"
        if sort_selection == "Department":
            sort_key = "department"
        elif sort_selection == "Date of Joining":
            sort_key = "doj"
        else:
            sort_key = "sr_no"

        staff_list = db.get_staff_with_gross(
            search=search if search else None,
            department=dept if dept else "All",
            sort_by=sort_key
        )

        for i, s in enumerate(staff_list):
            gross = s.get("latest_gross")
            gross_str = f"{gross:,.0f}" if gross else "—"
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            
            display_sr = s.get("sr_no", "") if sort_selection == "Serial No" else i + 1

            self.tree.insert("", "end", values=(
                s["id"], display_sr, s.get("name", ""), s.get("date_of_joining", ""),
                s.get("department", ""), s.get("designation", ""), gross_str, 
                s.get("payment_mode", ""), s.get("whatsapp", ""),
            ), tags=(tag,))

        self.counter_label.config(text=f"{len(staff_list)} staff members")

        if hasattr(self, "dept_combo"):
            current_dept = self.dept_var.get()
            base_depts = {"PHOENIX", "ADMIN"}
            db_depts = set(db.get_all_departments())
            all_depts = sorted(base_depts.union(db_depts))
            departments = ["All"] + all_depts
            self.dept_combo.config(values=departments)
            
            if current_dept in departments:
                self.dept_var.set(current_dept)
            else:
                self.dept_var.set("All")

    # ----------------------------------------
    # ADD/EDIT/DELETE ACTIONS
    # ----------------------------------------
    def open_add_dialog(self):
        StaffDialog(self.parent, on_save=self.refresh)

    def open_edit_dialog(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a staff member first.")
            return

        staff_id = int(self.tree.item(selection[0])["values"][0])
        staff = db.get_staff(staff_id)
        if not staff:
            messagebox.showerror("Error", "Staff record not found.")
            return

        StaffDialog(self.parent, staff=staff, on_save=self.refresh)

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a staff member first.")
            return

        values = self.tree.item(selection[0])["values"]
        staff_id = int(values[0])
        name = values[2]

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{name}'?\n\n"
            "This will not remove salary history."
        )
        if not confirm: return

        db.delete_staff(staff_id)
        self.refresh()

    # ----------------------------------------
    # BACKUP & IMPORT
    # ----------------------------------------
    def backup_database(self):
        try:
            backup_path = db.create_backup()
            messagebox.showinfo("Backup Created", f"Database backed up successfully.\n\nFile: {backup_path}")
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Error:\n{e}")

    def import_from_excel(self):
        from tkinter import filedialog
        import pandas as pd

        path = filedialog.askopenfilename(
            title="Select Excel Workbook",
            filetypes=[("Excel files", "*.xlsx *.xls")],
        )
        if not path: return

        try:
            all_sheets = pd.read_excel(path, sheet_name=None)
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")
            return

        combined_rows = []
        for sheet_name, df in all_sheets.items():
            df.columns = [str(c).strip() for c in df.columns]
            if "Name" not in df.columns: continue

            if "Department" not in df.columns:
                df["Department"] = sheet_name
            else:
                df["Department"] = df["Department"].fillna(sheet_name)

            valid_rows = [r for r in df.to_dict("records") if str(r.get("Name") or "").strip()]
            combined_rows.extend(valid_rows)

        if not combined_rows:
            messagebox.showwarning("No Data", "No valid staff rows found.")
            return

        confirm = messagebox.askyesno("Confirm Import", f"Found {len(combined_rows)} records.\nProceed?")
        if not confirm: return

        added_staff, added_salary, updated_salary = db.import_combined_data_from_excel(combined_rows)
        self.refresh()
        
        msg = f"Import Successful!\n\n✅ New Staff Added: {added_staff}\n✅ New Salaries Added: {added_salary}\n🔄 Salaries Updated: {updated_salary}"
        messagebox.showinfo("Import Complete", msg)

# ============================================
# STAFF DIALOG — Add / Edit
# ============================================
class StaffDialog:
    def __init__(self, parent, staff=None, on_save=None):
        self.staff = staff
        self.on_save = on_save
        self.is_edit = staff is not None

        if self.is_edit:
            self.auto_sr_no = staff.get("sr_no", "")
        else:
            self.auto_sr_no = db.get_next_sr_no()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Staff" if self.is_edit else "Add New Staff")
        self.dialog.geometry("560x720")
        self.dialog.configure(bg="#f0f4f8")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._build()
        if self.is_edit:
            self._populate()

    def _build(self):
        tk.Label(
            self.dialog, text="Edit Staff" if self.is_edit else "Add New Staff",
            font=("Segoe UI", 14, "bold"), bg="#f0f4f8", fg="#1a3a6b",
        ).pack(pady=15)

        container = tk.Frame(self.dialog, bg="#f0f4f8")
        container.pack(fill="both", expand=True, padx=20, pady=5)

        canvas = tk.Canvas(container, bg="#f0f4f8", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        form = tk.Frame(canvas, bg="#f0f4f8")

        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event): canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        def _bind_wheel(event): canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _unbind_wheel(event): canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _bind_wheel)
        canvas.bind("<Leave>", _unbind_wheel)
        
        self.entries = {}
        row = 0

        def add_field(label, key, default=""):
            nonlocal row
            tk.Label(form, text=label, font=("Segoe UI", 10, "bold"), bg="#f0f4f8", anchor="w").grid(row=row, column=0, sticky="w", pady=6, padx=(0, 10))
            e = tk.Entry(form, font=("Segoe UI", 10), width=35)
            e.insert(0, default)
            if key == "sr_no": e.config(state="readonly", bg="#e9ecef")
            e.grid(row=row, column=1, sticky="ew", pady=6)
            self.entries[key] = e
            row += 1

        form.grid_columnconfigure(1, weight=1)

        # --- Basic info ---
        tk.Label(form, text="— Basic Information —", font=("Segoe UI", 10, "bold italic"), bg="#f0f4f8", fg="#1a3a6b").grid(row=row, column=0, columnspan=2, pady=(10, 5), sticky="w")
        row += 1

        add_field("Sr # (auto)", "sr_no", "")
        add_field("Name *", "name", "")
        add_field("Date of Joining (dd.mm.yy)", "date_of_joining", "")
        add_field("Department", "department", "")
        add_field("Designation", "designation", "")

        # --- Contact ---
        tk.Label(form, text="— Contact Information —", font=("Segoe UI", 10, "bold italic"), bg="#f0f4f8", fg="#1a3a6b").grid(row=row, column=0, columnspan=2, pady=(15, 5), sticky="w")
        row += 1

        add_field("WhatsApp (+92...)", "whatsapp", "")
        add_field("Mobile", "mobile", "")
        add_field("CNIC", "cnic", "")
        add_field("Address", "address", "")
       
        # --- Security ---
        tk.Label(form, text="— Security Deduction (Refundable) —", font=("Segoe UI", 10, "bold italic"), bg="#f0f4f8", fg="#1a3a6b").grid(row=row, column=0, columnspan=2, pady=(15, 5), sticky="w")
        row += 1

        add_field("Total Security Amount", "security_total", "0")
        add_field("No. of Installments", "security_installments", "0")
        add_field("Per Month Deduction", "security_per_month", "0")
        add_field("Already Deducted (auto)", "security_already_deducted", "0")
        
        # --- Payment Mode ---
        tk.Label(form, text="— Payment Mode —", font=("Segoe UI", 10, "bold italic"), bg="#f0f4f8", fg="#1a3a6b").grid(row=row, column=0, columnspan=2, pady=(15, 5), sticky="w")
        row += 1

        tk.Label(form, text="Payment Mode:", font=("Segoe UI", 10, "bold"), bg="#f0f4f8", anchor="w").grid(row=row, column=0, sticky="w", pady=6, padx=(0, 10))
        mode_frame = tk.Frame(form, bg="#f0f4f8")
        mode_frame.grid(row=row, column=1, sticky="w", pady=6)

        self.payment_mode_var = tk.StringVar(value="Cash")
        tk.Radiobutton(mode_frame, text="Cash in Hand", variable=self.payment_mode_var, value="Cash", bg="#f0f4f8", font=("Segoe UI", 10), command=self._toggle_bank_fields).pack(side="left", padx=(0, 15))
        tk.Radiobutton(mode_frame, text="Bank Account", variable=self.payment_mode_var, value="Bank", bg="#f0f4f8", font=("Segoe UI", 10), command=self._toggle_bank_fields).pack(side="left")
        row += 1

        # Bank fields
        self.bank_name_label = tk.Label(form, text="Account Holder Name", font=("Segoe UI", 10, "bold"), bg="#f0f4f8", anchor="w")
        self.bank_name_entry = tk.Entry(form, font=("Segoe UI", 10), width=35)
        self.bank_account_label = tk.Label(form, text="Bank Account #", font=("Segoe UI", 10, "bold"), bg="#f0f4f8", anchor="w")
        self.bank_account_entry = tk.Entry(form, font=("Segoe UI", 10), width=35)

        self.entries["bank_name"] = self.bank_name_entry
        self.entries["bank_account"] = self.bank_account_entry
        self.bank_name_row = row
        self.bank_account_row = row + 1

        # --- Buttons ---
        btn_frame = tk.Frame(self.dialog, bg="#f0f4f8")
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="💾 Save", font=("Segoe UI", 11, "bold"), bg="#28a745", fg="white", padx=25, pady=10, cursor="hand2", command=self.save).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 11), bg="#6c757d", fg="white", padx=25, pady=10, cursor="hand2", command=self.dialog.destroy).pack(side="left", padx=5)

        self._toggle_bank_fields()

    def _toggle_bank_fields(self):
        if self.payment_mode_var.get() == "Bank":
            self.bank_name_label.grid(row=self.bank_name_row, column=0, sticky="w", pady=6, padx=(0, 10))
            self.bank_name_entry.grid(row=self.bank_name_row, column=1, sticky="ew", pady=6)
            self.bank_account_label.grid(row=self.bank_account_row, column=0, sticky="w", pady=6, padx=(0, 10))
            self.bank_account_entry.grid(row=self.bank_account_row, column=1, sticky="ew", pady=6)
        else:
            self.bank_name_label.grid_remove()
            self.bank_name_entry.grid_remove()
            self.bank_account_label.grid_remove()
            self.bank_account_entry.grid_remove()

    def _populate(self):
        if self.is_edit:
            for key, entry in self.entries.items():
                value = self.staff.get(key, "") or ""
                entry.delete(0, tk.END)
                entry.insert(0, str(value))
        else:
            self.entries["sr_no"].delete(0, tk.END)
            self.entries["sr_no"].insert(0, str(self.auto_sr_no))

        mode = self.staff.get("payment_mode", "Cash") if self.is_edit else "Cash"
        self.payment_mode_var.set(mode)
        self._toggle_bank_fields()

    def save(self):
        name = self.entries["name"].get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required!")
            return

        try:
            sr_no = int(self.entries["sr_no"].get() or 0)
        except ValueError:
            sr_no = 0

        payment_mode = self.payment_mode_var.get()

        # Yahan se basic_pay hata diya gaya hai
        data = {
            "sr_no": sr_no,
            "name": name,
            "date_of_joining": self.entries["date_of_joining"].get().strip(),
            "department": self.entries["department"].get().strip(),
            "designation": self.entries["designation"].get().strip(),
            "whatsapp": self.entries["whatsapp"].get().strip(),
            "mobile": self.entries["mobile"].get().strip(),
            "cnic": self.entries["cnic"].get().strip(),
            "address": self.entries["address"].get().strip(),
            "payment_mode": payment_mode,
            "bank_name": self.entries["bank_name"].get().strip() if payment_mode == "Bank" else "",
            "bank_account": self.entries["bank_account"].get().strip() if payment_mode == "Bank" else "",
            "security_total": float(self.entries["security_total"].get() or 0),
            "security_installments": int(self.entries["security_installments"].get() or 0),
            "security_per_month": float(self.entries["security_per_month"].get() or 0),
            "security_already_deducted": float(self.entries["security_already_deducted"].get() or 0),
        }

        if self.is_edit:
            db.update_staff(self.staff["id"], **data)
            messagebox.showinfo("Success", f"'{name}' updated successfully.")
        else:
            # Naye staff ke liye basic_pay 0 set kar rahe hain
            db.add_staff(basic_pay=0, **data)
            messagebox.showinfo("Success", f"'{name}' added successfully.")

        self.dialog.destroy()
        if self.on_save:
            self.on_save()
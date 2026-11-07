"""
Settings tab — password change + salary rules.
"""
import tkinter as tk
from tkinter import messagebox

from src import auth
from src import app_settings


class SettingsTab:
    def __init__(self, parent):
        self.parent = parent
        self._build_ui()

    # ----------------------------------------
    # UI
    # ----------------------------------------
    def _build_ui(self):
        # ---- Outer scrollable container ----
        outer = tk.Frame(self.parent, bg="#f0f4f8")
        outer.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(
            outer, bg="#f0f4f8", highlightthickness=0,
            takefocus=1
        )
        scrollbar = tk.Scrollbar(outer, orient="vertical",
                                 command=self._canvas.yview)

        # ---- Inner frame (holds all content) ----
        self._content = tk.Frame(self._canvas, bg="#f0f4f8")

        canvas_window = self._canvas.create_window(
            (0, 0), window=self._content, anchor="nw"
        )

        # Sync inner frame width to canvas width
        def _sync_width(event):
            self._canvas.itemconfig(canvas_window, width=event.width)

        self._canvas.bind("<Configure>", _sync_width)

        # Update scroll region when content changes
        self._content.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")
            )
        )

        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel
        def _on_mousewheel(event):
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(event):
            self._canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(event):
            self._canvas.unbind_all("<MouseWheel>")

        self._canvas.bind("<Enter>", _bind_wheel)
        self._canvas.bind("<Leave>", _unbind_wheel)

        # ---- Title ----
        title_frame = tk.Frame(self._content, bg="#f0f4f8")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))

        tk.Label(
            title_frame, text="⚙️ Settings",
            font=("Segoe UI", 16, "bold"),
            bg="#f0f4f8", fg="#1a3a6b",
        ).pack(anchor="w")

        tk.Label(
            title_frame, text="Manage application settings",
            font=("Segoe UI", 10, "italic"),
            bg="#f0f4f8", fg="#556677",
        ).pack(anchor="w")

        # Separator
        tk.Frame(self._content, bg="#c9d6e8", height=1).pack(
            fill="x", padx=20, pady=10
        )

        # Change Password section
        self._build_change_password()

        # Separator
        tk.Frame(self._content, bg="#c9d6e8", height=1).pack(
            fill="x", padx=20, pady=10
        )

        # Salary Rules section
        self._build_salary_rules()

        # ---- Force scroll to top after UI settles ----
        def _reset_scroll():
            self._canvas.update_idletasks()
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
            self._canvas.yview_moveto(0.0)
            self._canvas.focus_set()

        # Run at multiple intervals for reliability
        self.parent.after(50, _reset_scroll)
        self.parent.after(200, _reset_scroll)
        self.parent.after(500, _reset_scroll)

    # ----------------------------------------
    # CHANGE PASSWORD
    # ----------------------------------------
    def _build_change_password(self):
        # Section container — always fill width
        section = tk.Frame(self._content, bg="#ffffff",
                           relief="solid", bd=1)
        section.pack(fill="x", padx=20, pady=10)

        # Header
        header = tk.Frame(section, bg="#1a3a6b", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="🔒 Change Password",
            font=("Segoe UI", 12, "bold"),
            bg="#1a3a6b", fg="white",
        ).pack(side="left", padx=15, pady=8)

        # Body
        body = tk.Frame(section, bg="#ffffff")
        body.pack(fill="x", padx=20, pady=15)

        self.entries = {}

        def add_field(label, key, show="•"):
            row = tk.Frame(body, bg="#ffffff")
            row.pack(fill="x", pady=6)

            tk.Label(
                row, text=label,
                font=("Segoe UI", 10, "bold"),
                bg="#ffffff", anchor="w", width=22,
            ).pack(side="left")

            entry = tk.Entry(
                row, font=("Segoe UI", 11), width=30,
                show=show,
            )
            entry.pack(side="left", padx=10, ipady=3, fill="x", expand=True)
            self.entries[key] = entry

        add_field("Current Password:", "current")
        add_field("New Password:", "new")
        add_field("Confirm New Password:", "confirm")

        tk.Label(
            body, text="Password must be at least 4 characters.",
            font=("Segoe UI", 8, "italic"),
            bg="#ffffff", fg="#8899aa",
        ).pack(anchor="w", pady=(5, 0))

        # Show/Hide checkbox
        show_var = tk.BooleanVar(value=False)

        def toggle_show():
            if show_var.get():
                for e in self.entries.values():
                    e.config(show="")
            else:
                for e in self.entries.values():
                    e.config(show="•")

        tk.Checkbutton(
            body, text="Show passwords",
            variable=show_var,
            font=("Segoe UI", 9),
            bg="#ffffff",
            command=toggle_show,
        ).pack(anchor="w", pady=(5, 0))

        # Buttons
        btn_frame = tk.Frame(body, bg="#ffffff")
        btn_frame.pack(anchor="w", pady=(15, 5))

        tk.Button(
            btn_frame, text="💾 Change Password",
            font=("Segoe UI", 11, "bold"),
            bg="#28a745", fg="white",
            padx=20, pady=8, cursor="hand2",
            command=self.change_password,
        ).pack(side="left")

        tk.Button(
            btn_frame, text="Clear",
            font=("Segoe UI", 11),
            bg="#6c757d", fg="white",
            padx=20, pady=8, cursor="hand2",
            command=self.clear_fields,
        ).pack(side="left", padx=8)

        # Status
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(
            body, textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg="#ffffff", fg="#dc3545",
        )
        self.status_label.pack(anchor="w", pady=(10, 0))

    # ----------------------------------------
    # SALARY RULES
    # ----------------------------------------
    def _build_salary_rules(self):
        # Section container — always fill width
        section = tk.Frame(self._content, bg="#ffffff",
                           relief="solid", bd=1)
        section.pack(fill="x", padx=20, pady=10)

        # Header
        header = tk.Frame(section, bg="#1a3a6b", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="⚙️ Salary Rules (Fixed Values)",
            font=("Segoe UI", 12, "bold"),
            bg="#1a3a6b", fg="white",
        ).pack(side="left", padx=15, pady=8)

        # Body
        body = tk.Frame(section, bg="#ffffff")
        body.pack(fill="x", padx=20, pady=15)

        self.rule_entries = {}

        def add_rule(label, key, default):
            row = tk.Frame(body, bg="#ffffff")
            row.pack(fill="x", pady=6)

            tk.Label(
                row, text=label,
                font=("Segoe UI", 10, "bold"),
                bg="#ffffff", anchor="w", width=32,
            ).pack(side="left")

            entry = tk.Entry(row, font=("Segoe UI", 11), width=15)
            entry.insert(0, str(default))
            entry.pack(side="left", padx=10, ipady=3)
            self.rule_entries[key] = entry

        # Load current values
        current = app_settings.load_settings()

        add_rule("Late Arrival Fine (Rs.):",
                 "late_arrival_fine",
                 current.get("late_arrival_fine", 100))

        add_rule("GP Fund Monthly (Rs.):",
                 "gp_fund_monthly",
                 current.get("gp_fund_monthly", 200))

        add_rule("Overtime Rate per Hour (Rs.):",
                 "overtime_rate_per_hour",
                 current.get("overtime_rate_per_hour", 200))

        add_rule("Social Security (Rs.):",
                 "social_security_amount",
                 current.get("social_security_amount", 1300))
                 
        add_rule("OAB (Rs.):",
                 "oab_amount",
                 current.get("oab_amount", 480))
                 
        
        # Info text
        tk.Label(
            body,
            text="These values apply to all NEW salary entries.\n"
                 "Already-saved salaries will not change.",
            font=("Segoe UI", 8, "italic"),
            bg="#ffffff", fg="#8899aa",
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        # Buttons
        btn_frame = tk.Frame(body, bg="#ffffff")
        btn_frame.pack(anchor="w", pady=(15, 5))

        tk.Button(
            btn_frame, text="💾 Save Rules",
            font=("Segoe UI", 11, "bold"),
            bg="#28a745", fg="white",
            padx=20, pady=8, cursor="hand2",
            command=self.save_salary_rules,
        ).pack(side="left")

        tk.Button(
            btn_frame, text="Reset to Defaults",
            font=("Segoe UI", 11),
            bg="#6c757d", fg="white",
            padx=20, pady=8, cursor="hand2",
            command=self.reset_salary_rules,
        ).pack(side="left", padx=8)

        # Status
        self.rules_status_var = tk.StringVar(value="")
        self.rules_status_label = tk.Label(
            body, textvariable=self.rules_status_var,
            font=("Segoe UI", 9),
            bg="#ffffff", fg="#dc3545",
        )
        self.rules_status_label.pack(anchor="w", pady=(10, 0))
        # Separator
        tk.Frame(self._content, bg="#c9d6e8", height=1).pack(
            fill="x", padx=20, pady=10
        )

        # Bank Transfer Settings section
        self._build_bank_settings()
    # ----------------------------------------
    # BANK TRANSFER SETTINGS
    # ----------------------------------------
    def _build_bank_settings(self):
        section = tk.Frame(self._content, bg="#ffffff",
                           relief="solid", bd=1)
        section.pack(fill="x", padx=20, pady=10)

        # Header
        header = tk.Frame(section, bg="#1a3a6b", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="🏦 Bank Transfer Settings",
            font=("Segoe UI", 12, "bold"),
            bg="#1a3a6b", fg="white",
        ).pack(side="left", padx=15, pady=8)

        # Body
        body = tk.Frame(section, bg="#ffffff")
        body.pack(fill="x", padx=20, pady=15)

        self.bank_entries = {}

        def add_field(label, key, default, width=40):
            row = tk.Frame(body, bg="#ffffff")
            row.pack(fill="x", pady=6)

            tk.Label(
                row, text=label,
                font=("Segoe UI", 10, "bold"),
                bg="#ffffff", anchor="w", width=28,
            ).pack(side="left")

            entry = tk.Entry(row, font=("Segoe UI", 11), width=width)
            entry.insert(0, str(default))
            entry.pack(side="left", padx=10, ipady=3)
            self.bank_entries[key] = entry

        # Load current values
        current = app_settings.load_settings()

        add_field("School Account Number:",
                  "school_account",
                  current.get("school_account", "1007862"))

        add_field("Bank Name & Branch:",
                  "bank_name",
                  current.get("bank_name",
                              "MCB Satellite Town Branch Sargodha"),
                  width=50)

        # Info
        tk.Label(
            body,
            text="These values are used in the Bank Transfer Statement report.",
            font=("Segoe UI", 8, "italic"),
            bg="#ffffff", fg="#8899aa",
        ).pack(anchor="w", pady=(8, 0))

        # Buttons
        btn_frame = tk.Frame(body, bg="#ffffff")
        btn_frame.pack(anchor="w", pady=(15, 5))

        tk.Button(
            btn_frame, text="💾 Save Bank Settings",
            font=("Segoe UI", 11, "bold"),
            bg="#28a745", fg="white",
            padx=20, pady=8, cursor="hand2",
            command=self.save_bank_settings,
        ).pack(side="left")

        # Status
        self.bank_status_var = tk.StringVar(value="")
        self.bank_status_label = tk.Label(
            body, textvariable=self.bank_status_var,
            font=("Segoe UI", 9),
            bg="#ffffff", fg="#dc3545",
        )
        self.bank_status_label.pack(anchor="w", pady=(10, 0))

    def save_bank_settings(self):
        try:
            new_values = {}
            for key, entry in self.bank_entries.items():
                raw = entry.get().strip()
                if not raw:
                    raise ValueError(f"{key} cannot be empty")
                new_values[key] = raw

            app_settings.update(**new_values)
            self.bank_status_label.config(fg="#28a745")
            self.bank_status_var.set("✅ Bank settings saved.")
            messagebox.showinfo(
                "Success",
                "Bank transfer settings updated."
            )
        except ValueError as e:
            self.bank_status_label.config(fg="#dc3545")
            self.bank_status_var.set(f"❌ Invalid value: {e}")
    # ----------------------------------------
    # ACTIONS — PASSWORD
    # ----------------------------------------
    def change_password(self):
        current = self.entries["current"].get()
        new = self.entries["new"].get()
        confirm = self.entries["confirm"].get()

        if not current or not new or not confirm:
            self._show_status("Please fill all three fields.", "error")
            return

        if not auth.verify_password(current):
            self._show_status("Current password is incorrect.", "error")
            return

        if new != confirm:
            self._show_status("New passwords do not match.", "error")
            return

        if len(new) < 4:
            self._show_status("New password must be at least 4 characters.", "error")
            return

        if new == current:
            self._show_status("New password must be different.", "error")
            return

        if auth.change_password(new):
            self._show_status("Password changed successfully!", "success")
            self.clear_fields()
            messagebox.showinfo(
                "Success",
                "Password changed successfully.\n\n"
                "Use the new password next time you log in."
            )
        else:
            self._show_status("Could not change password.", "error")

    def clear_fields(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.status_var.set("")

    def _show_status(self, message, kind):
        self.status_var.set(message)
        if kind == "success":
            self.status_label.config(fg="#28a745")
        else:
            self.status_label.config(fg="#dc3545")

    # ----------------------------------------
    # ACTIONS — SALARY RULES
    # ----------------------------------------
    def save_salary_rules(self):
        try:
            new_values = {}
            for key, entry in self.rule_entries.items():
                raw = entry.get().strip()
                if not raw:
                    raise ValueError(f"{key} cannot be empty")
                new_values[key] = float(raw)

            app_settings.update(**new_values)
            self.rules_status_label.config(fg="#28a745")
            self.rules_status_var.set("✅ Settings saved successfully.")
            messagebox.showinfo(
                "Success",
                "Salary rules updated.\n\n"
                "New values will apply to salaries entered from now on."
            )
        except ValueError as e:
            self.rules_status_label.config(fg="#dc3545")
            self.rules_status_var.set(f"❌ Invalid value: {e}")

    def reset_salary_rules(self):
        confirm = messagebox.askyesno(
            "Reset to Defaults",
            "Reset salary rules to default values?\n\n"
            "Late Arrival Fine: 100\n"
            "GP Fund: 200\n"
            "Overtime Rate: 200/hr\n"
            "Social Security: 1300\n"
            "OAB: 480\n"
            "Absentee Fine: 5000"
        )
        if not confirm:
            return

        app_settings.save_settings(app_settings.DEFAULTS)

        # Refresh entries
        self.rule_entries["late_arrival_fine"].delete(0, tk.END)
        self.rule_entries["late_arrival_fine"].insert(0, "100")
        self.rule_entries["gp_fund_monthly"].delete(0, tk.END)
        self.rule_entries["gp_fund_monthly"].insert(0, "200")
        self.rule_entries["overtime_rate_per_hour"].delete(0, tk.END)
        self.rule_entries["overtime_rate_per_hour"].insert(0, "200")
        self.rule_entries["social_security_amount"].delete(0, tk.END)
        self.rule_entries["social_security_amount"].insert(0, "1300")
        self.rule_entries["oab_amount"].delete(0, tk.END)
        self.rule_entries["oab_amount"].insert(0, "480")
        
        self.rules_status_label.config(fg="#28a745")
        self.rules_status_var.set("✅ Reset to defaults.")
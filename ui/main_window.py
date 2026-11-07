"""
Main application window with tabs.
"""
import tkinter as tk
from tkinter import ttk
from src.config import SCHOOL_NAME, DEFAULT_MONTH, DEFAULT_YEAR
from ui.staff_tab import StaffTab
from ui.salary_tab import SalaryTab
from ui.payslip_tab import PayslipTab
from ui.whatsapp_tab import WhatsAppTab
from ui.reports_tab import ReportsTab
from ui.settings_tab import SettingsTab
from tkinter import ttk, messagebox

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{SCHOOL_NAME} — Salary Manager")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f4f8")

        self._build_header()
        self._build_tabs()
        self._build_status_bar()

        # Handle window close (X button) — auto-backup
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ----------------------------------------
    # HEADER
    # ----------------------------------------
    def _build_header(self):
        header = tk.Frame(self.root, bg="#1a3a6b", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        # Center block (title + subtitle)
        center = tk.Frame(header, bg="#1a3a6b")
        center.pack(expand=True)

        title = tk.Label(
            center,
            text=SCHOOL_NAME,
            font=("Segoe UI", 18, "bold"),
            bg="#1a3a6b", fg="white",
        )
        title.pack(pady=(10, 0))

        subtitle = tk.Label(
            center,
            text="Salary Statement Manager",
            font=("Segoe UI", 11),
            bg="#1a3a6b", fg="#c9d6e8",
        )
        subtitle.pack()

        # Logout button (top-right)
        logout_btn = tk.Button(
            header,
            text="🚪 Logout",
            font=("Segoe UI", 10, "bold"),
            bg="#dc3545", fg="white",
            activebackground="#c82333", activeforeground="white",
            padx=15, pady=6, cursor="hand2",
            relief="flat", bd=0,
            command=self.logout,
        )
        logout_btn.place(relx=1.0, rely=0.5, anchor="e", x=-15)
    def on_close(self):
        """Handle window close (X button) — runs auto-backup first."""
        try:
            from src import database as db
            path = db.auto_backup()
            if path:
                print(f"Auto-backup created: {path}")
        except Exception as e:
            print(f"Auto-backup error: {e}")

        # Destroy window
        self.root.destroy()
    # ----------------------------------------
    # TABS
    # ----------------------------------------
    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1 — Staff
        self.staff_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.staff_tab, text="  👥  Staff  ")
        StaffTab(self.staff_tab)

        # Tab 2 — Salary Entry
        self.salary_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.salary_tab, text="  💰  Salary Entry  ")
        SalaryTab(self.salary_tab)

                # Tab 3 — Payslips
        self.payslip_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.payslip_tab, text="  📄  Payslips  ")
        PayslipTab(self.payslip_tab)

                # Tab 4 — WhatsApp
        self.whatsapp_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.whatsapp_tab, text="  📤  WhatsApp  ")
        WhatsAppTab(self.whatsapp_tab)

                # Tab 5 — Reports
        self.reports_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.reports_tab, text="  📊  Reports  ")
        ReportsTab(self.reports_tab)

        # Tab 6 — Settings
        self.settings_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.settings_tab, text="  ⚙️  Settings  ")
        SettingsTab(self.settings_tab)

        # Start on Staff tab (index 0 — first tab)
        self.notebook.select(0)
        
    def _build_placeholder(self, parent, text):
        tk.Label(
            parent, text=text,
            font=("Segoe UI", 16), bg="#f0f4f8", fg="#8899aa",
        ).pack(pady=50)


    # ----------------------------------------
    # STATUS BAR
    # ----------------------------------------
    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg="#e0e8f0", height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.status_label = tk.Label(
            bar,
            text=f"Ready  |  {DEFAULT_MONTH} {DEFAULT_YEAR}",
            font=("Segoe UI", 9),
            bg="#e0e8f0", fg="#556677",
            anchor="w",
        )
        self.status_label.pack(side="left", padx=10, fill="y")
        
    # ----------------------------------------
    # LOGOUT
    # ----------------------------------------
    def logout(self):
        """Confirm and logout — return to login screen."""
        confirm = messagebox.askyesno(
            "Logout",
            "Are you sure you want to logout?\n\n"
            "Any unsaved changes will be lost."
        )
        if not confirm:
            return

        # Close current window
        self.root.destroy()

        # Launch login + main window again (same process)
        from ui.login import LoginWindow
        from ui.main_window import MainWindow

        login = LoginWindow()
        if not login.run():
            return

        # Login successful — reopen main window
        new_root = tk.Tk()
        new_app = MainWindow(new_root)
        new_root.mainloop()

        # Close the main window
        self.root.destroy()

        # Re-launch application (login will appear again)
        import subprocess
        import sys
        from pathlib import Path

        if getattr(sys, "frozen", False):
            # Running as EXE
            subprocess.Popen([sys.executable])
        else:
            # Running as script
            project_root = Path(__file__).resolve().parent.parent
            subprocess.Popen([sys.executable, str(project_root / "main.py")])
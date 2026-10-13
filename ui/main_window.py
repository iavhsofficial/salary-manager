"""
Main application window with tabs.
"""
import tkinter as tk
from tkinter import ttk
from src.config import SCHOOL_NAME, DEFAULT_MONTH, DEFAULT_YEAR


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{SCHOOL_NAME} — Salary Manager")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f4f8")

        self._build_header()
        self._build_tabs()
        self._build_status_bar()

    # ----------------------------------------
    # HEADER
    # ----------------------------------------
    def _build_header(self):
        header = tk.Frame(self.root, bg="#1a3a6b", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text=SCHOOL_NAME,
            font=("Segoe UI", 18, "bold"),
            bg="#1a3a6b", fg="white",
        )
        title.pack(pady=(10, 0))

        subtitle = tk.Label(
            header,
            text="Salary Statement Manager",
            font=("Segoe UI", 11),
            bg="#1a3a6b", fg="#c9d6e8",
        )
        subtitle.pack()

    # ----------------------------------------
    # TABS
    # ----------------------------------------
    def _build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1 — Staff
        self.staff_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.staff_tab, text="  👥  Staff  ")
        self._build_staff_placeholder()

        # Tab 2 — Salary Entry
        self.salary_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.salary_tab, text="  💰  Salary Entry  ")
        self._build_placeholder(self.salary_tab, "Salary Entry — Coming Next")

        # Tab 3 — Payslips
        self.payslip_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.payslip_tab, text="  📄  Payslips  ")
        self._build_placeholder(self.payslip_tab, "Payslip Generation — Coming Next")

        # Tab 4 — WhatsApp
        self.whatsapp_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.whatsapp_tab, text="  📤  WhatsApp  ")
        self._build_placeholder(self.whatsapp_tab, "WhatsApp Sending — Coming Next")

        # Tab 5 — Reports
        self.reports_tab = tk.Frame(self.notebook, bg="#f0f4f8")
        self.notebook.add(self.reports_tab, text="  📊  Reports  ")
        self._build_placeholder(self.reports_tab, "Reports — Coming Next")

    def _build_placeholder(self, parent, text):
        tk.Label(
            parent, text=text,
            font=("Segoe UI", 16), bg="#f0f4f8", fg="#8899aa",
        ).pack(pady=50)

    def _build_staff_placeholder(self):
        """Staff tab — placeholder for now, will be replaced."""
        tk.Label(
            self.staff_tab,
            text="Staff Management — Coming Next",
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
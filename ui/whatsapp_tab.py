"""
WhatsApp tab — click-to-chat with PDF opener.
Semi-automatic: opens WhatsApp chat + PDF folder.
User drags PDF into WhatsApp and sends, then clicks Next.
"""
import os
import sys
import subprocess
import urllib.parse
import tkinter as tk
from tkinter import ttk, messagebox

from src.config import (
    MONTHS, DEFAULT_MONTH, DEFAULT_YEAR, get_payslip_dir
)
from src import database as db


class WhatsAppTab:
    def __init__(self, parent):
        self.parent = parent
        self.staff_queue = []      # list of dicts
        self.current_index = -1    # index of current staff
        self.month = DEFAULT_MONTH
        self.year = DEFAULT_YEAR

        self._build_ui()

    # ----------------------------------------
    # UI
    # ----------------------------------------
    def _build_ui(self):
        # Top toolbar
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
            top, text="🔄 Load Queue",
            font=("Segoe UI", 10, "bold"),
            bg="#007bff", fg="white",
            padx=15, pady=5, cursor="hand2",
            command=self.load_queue,
        ).pack(side="left", padx=20)

        # Info
        self.info_label = tk.Label(
            self.parent,
            text="Select month and click 'Load Queue' to begin.",
            font=("Segoe UI", 10, "italic"),
            bg="#f0f4f8", fg="#556677",
        )
        self.info_label.pack(pady=(0, 10))

        # Current staff display
        current_frame = tk.Frame(self.parent, bg="#ffffff", relief="solid", bd=1)
        current_frame.pack(fill="x", padx=10, pady=10)

        self.current_label = tk.Label(
            current_frame,
            text="No staff loaded",
            font=("Segoe UI", 14, "bold"),
            bg="#ffffff", fg="#1a3a6b",
            pady=15,
        )
        self.current_label.pack()

        self.current_number_label = tk.Label(
            current_frame,
            text="",
            font=("Segoe UI", 11),
            bg="#ffffff", fg="#556677",
        )
        self.current_number_label.pack()

        self.current_progress_label = tk.Label(
            current_frame,
            text="",
            font=("Segoe UI", 10, "italic"),
            bg="#ffffff", fg="#8899aa",
        )
        self.current_progress_label.pack(pady=(5, 15))

        # Action buttons
        action_frame = tk.Frame(self.parent, bg="#f0f4f8")
        action_frame.pack(pady=10)

        self.open_btn = tk.Button(
            action_frame, text="📱 Open WhatsApp + PDF",
            font=("Segoe UI", 12, "bold"),
            bg="#25D366", fg="white",
            padx=25, pady=12, cursor="hand2",
            command=self.open_current,
            state="disabled",
        )
        self.open_btn.pack(side="left", padx=5)

        self.next_btn = tk.Button(
            action_frame, text="➡️ Next Staff",
            font=("Segoe UI", 12, "bold"),
            bg="#007bff", fg="white",
            padx=25, pady=12, cursor="hand2",
            command=self.next_staff,
            state="disabled",
        )
        self.next_btn.pack(side="left", padx=5)

        self.skip_btn = tk.Button(
            action_frame, text="⏭️ Skip",
            font=("Segoe UI", 12),
            bg="#6c757d", fg="white",
            padx=25, pady=12, cursor="hand2",
            command=self.skip_staff,
            state="disabled",
        )
        self.skip_btn.pack(side="left", padx=5)

        # Queue list
        queue_label = tk.Label(
            self.parent, text="Queue:",
            font=("Segoe UI", 10, "bold"),
            bg="#f0f4f8", anchor="w",
        )
        queue_label.pack(fill="x", padx=15, pady=(15, 5))

        queue_frame = tk.Frame(self.parent, bg="#f0f4f8")
        queue_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = ("#", "Name", "WhatsApp", "Status")
        self.queue_tree = ttk.Treeview(
            queue_frame, columns=cols,
            show="headings", height=8,
        )
        widths = [50, 250, 140, 150]
        for c, w in zip(cols, widths):
            self.queue_tree.heading(c, text=c)
            self.queue_tree.column(c, width=w, anchor="center")

        vsb = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=vsb.set)
        self.queue_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        queue_frame.grid_rowconfigure(0, weight=1)
        queue_frame.grid_columnconfigure(0, weight=1)

    # ----------------------------------------
    # LOAD QUEUE
    # ----------------------------------------
    def load_queue(self):
        month = self.month_var.get()
        if not month or month == "Select Month":
            messagebox.showwarning("Month Required", "Please select a month first.")
            return

        self.month = month
        self.year = year

        # Get all staff with salary entered for this month
        rows = db.get_all_salaries_for_month(month, year)
        folder = get_payslip_dir(month, year)

        for s in rows:
            name = s.get("name", "")
            whatsapp = (s.get("whatsapp") or "").strip()
            net_pay = s.get("net_pay") or 0

            # Skip if no salary entered
            if not net_pay:
                continue

            # Check PDF exists
            safe_name = name.replace(" ", "_")
            pdf_path = folder / f"{safe_name}.pdf"
            has_pdf = pdf_path.exists()

            # Check whatsapp number
            if not whatsapp:
                status = "⚠ No WhatsApp"
            elif not has_pdf:
                status = "⚠ No PDF"
            else:
                status = "✅ Ready"

            self.staff_queue.append({
                "staff_id": s["staff_id"],
                "name": name,
                "whatsapp": whatsapp,
                "pdf_path": str(pdf_path) if has_pdf else "",
                "status": status,
            })

        # Populate tree
        for i, item in enumerate(self.staff_queue):
            self.queue_tree.insert("", "end", iid=str(i), values=(
                i + 1,
                item["name"],
                item["whatsapp"],
                item["status"],
            ))

        total = len(self.staff_queue)
        ready = sum(1 for s in self.staff_queue if s["status"] == "✅ Ready")

        self.info_label.config(
            text=f"{month} {year} — {ready} ready out of {total} staff"
        )

        if total == 0:
            messagebox.showwarning(
                "No Data",
                f"No salary records found for {month} {year}.\n\n"
                "Please enter salaries first."
            )
            return

        # Start from first ready staff
        self.current_index = -1
        self._move_to_next_ready()
        self._update_display()

    # ----------------------------------------
    # FIND NEXT READY STAFF
    # ----------------------------------------
    def _move_to_next_ready(self):
        """Move current_index to next staff with status='Ready'."""
        for i in range(self.current_index + 1, len(self.staff_queue)):
            if self.staff_queue[i]["status"] == "✅ Ready":
                self.current_index = i
                return True
        return False

    # ----------------------------------------
    # UPDATE DISPLAY
    # ----------------------------------------
    def _update_display(self):
        if self.current_index < 0 or self.current_index >= len(self.staff_queue):
            self.current_label.config(text="🎉 All Done!")
            self.current_number_label.config(text="No more staff in queue.")
            self.current_progress_label.config(text="")
            self.open_btn.config(state="disabled")
            self.next_btn.config(state="disabled")
            self.skip_btn.config(state="disabled")
            return

        item = self.staff_queue[self.current_index]
        self.current_label.config(text=item["name"])
        self.current_number_label.config(text=f"📱 {item['whatsapp']}")

        ready_count = sum(1 for s in self.staff_queue if s["status"] == "✅ Ready")
        done_count = sum(1 for s in self.staff_queue if s["status"] == "✅ Sent")

        self.current_progress_label.config(
            text=f"Staff {self.current_index + 1} of {len(self.staff_queue)}  |  "
                 f"Sent: {done_count}  |  Remaining: {ready_count}"
        )

        self.open_btn.config(state="normal")
        self.next_btn.config(state="normal")
        self.skip_btn.config(state="normal")

        # Highlight in queue
        self.queue_tree.selection_remove(self.queue_tree.selection())
        if str(self.current_index) in self.queue_tree.get_children():
            self.queue_tree.selection_set(str(self.current_index))
            self.queue_tree.see(str(self.current_index))

    # ----------------------------------------
    # OPEN WHATSAPP + PDF
    # ----------------------------------------
    def open_current(self):
        if self.current_index < 0:
            return

        item = self.staff_queue[self.current_index]
        name = item["name"]
        whatsapp = item["whatsapp"]
        pdf_path = item["pdf_path"]

        # Clean phone number
        phone = "".join(c for c in whatsapp if c.isdigit() or c == "+")
        if phone.startswith("+"):
            phone = phone[1:]
        if phone.startswith("0"):
            phone = "92" + phone[1:]  # Pakistan country code

        # Message caption
        message = (
            f"Dear {name},\n\n"
            f"Please find your payslip for {self.month} {self.year} attached.\n\n"
            f"Regards,\nAccounts Department\n"
            f"Islamic Alta Vista High School"
        )
        encoded_message = urllib.parse.quote(message)

        # WhatsApp click-to-chat URL
        wa_url = f"https://wa.me/{phone}?text={encoded_message}"

        # Open WhatsApp in default browser
        try:
            os.startfile(wa_url)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open WhatsApp:\n{e}")
            return

        # Open PDF in default viewer (after a short delay)
        if pdf_path and os.path.exists(pdf_path):
            self.parent.after(1200, lambda: self._open_pdf(pdf_path))

        # Mark status
        item["status"] = "📤 Opened"
        self.queue_tree.set(str(self.current_index), "Status", "📤 Opened")

    def _open_pdf(self, pdf_path):
        """Open PDF in default viewer."""
        try:
            os.startfile(pdf_path)
        except Exception as e:
            print(f"Could not open PDF: {e}")

    # ----------------------------------------
    # NEXT STAFF
    # ----------------------------------------
    def next_staff(self):
        # Mark current as sent
        if 0 <= self.current_index < len(self.staff_queue):
            self.staff_queue[self.current_index]["status"] = "✅ Sent"
            self.queue_tree.set(
                str(self.current_index), "Status", "✅ Sent"
            )

        if self._move_to_next_ready():
            self._update_display()
        else:
            self._update_display()

    # ----------------------------------------
    # SKIP
    # ----------------------------------------
    def skip_staff(self):
        if 0 <= self.current_index < len(self.staff_queue):
            self.staff_queue[self.current_index]["status"] = "⏭️ Skipped"
            self.queue_tree.set(
                str(self.current_index), "Status", "⏭️ Skipped"
            )

        if self._move_to_next_ready():
            self._update_display()
        else:
            self._update_display()
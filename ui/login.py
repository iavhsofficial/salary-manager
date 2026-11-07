"""
Login window — password prompt before accessing main application.
"""
import tkinter as tk
from tkinter import messagebox

from src.config import SCHOOL_NAME
from src import auth


class LoginWindow:
    def __init__(self):
        self.authenticated = False
        self.attempts = 0
        self.max_attempts = 3

        self.root = tk.Tk()
        self.root.title("Login — Salary Manager")
        self.root.configure(bg="#f0f4f8")
        self.root.resizable(False, False)

        # Center window
        w, h = 420, 320
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2 - 40
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        # Prevent close without login (optional)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build()

    def _build(self):
        # Header
        header = tk.Frame(self.root, bg="#1a3a6b", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text=SCHOOL_NAME,
            font=("Segoe UI", 13, "bold"),
            bg="#1a3a6b", fg="white",
        ).pack(pady=(15, 0))

        tk.Label(
            header, text="Salary Manager — Login",
            font=("Segoe UI", 10),
            bg="#1a3a6b", fg="#c9d6e8",
        ).pack()

        # Body
        body = tk.Frame(self.root, bg="#f0f4f8")
        body.pack(fill="both", expand=True, padx=30, pady=25)

        tk.Label(
            body, text="🔒 Enter Password",
            font=("Segoe UI", 12, "bold"),
            bg="#f0f4f8", fg="#1a3a6b",
        ).pack(pady=(0, 15))

        self.password_var = tk.StringVar()
        entry = tk.Entry(
            body, textvariable=self.password_var,
            font=("Segoe UI", 12), width=25, show="•",
            justify="center",
        )
        entry.pack(pady=5, ipady=6)
        entry.focus_set()
        entry.bind("<Return>", lambda e: self.attempt_login())

        # Hint (only if default password still in use)
        if auth.is_default_password():
            tk.Label(
                body, text="Default password: iavhs2026",
                font=("Segoe UI", 8, "italic"),
                bg="#f0f4f8", fg="#8899aa",
            ).pack(pady=(5, 0))

        # Buttons
        btn_frame = tk.Frame(body, bg="#f0f4f8")
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame, text="🔓 Login",
            font=("Segoe UI", 11, "bold"),
            bg="#28a745", fg="white",
            padx=25, pady=8, cursor="hand2",
            command=self.attempt_login,
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="Exit",
            font=("Segoe UI", 11),
            bg="#6c757d", fg="white",
            padx=25, pady=8, cursor="hand2",
            command=self.on_close,
        ).pack(side="left", padx=5)

        # Status label
        self.status_var = tk.StringVar(value="")
        tk.Label(
            body, textvariable=self.status_var,
            font=("Segoe UI", 9), bg="#f0f4f8", fg="#dc3545",
        ).pack()

    def attempt_login(self):
        pwd = self.password_var.get()

        if not pwd:
            self.status_var.set("Please enter password.")
            return

        if auth.verify_password(pwd):
            self.authenticated = True
            self.root.destroy()
        else:
            self.attempts += 1
            remaining = self.max_attempts - self.attempts
            if remaining <= 0:
                messagebox.showerror(
                    "Access Denied",
                    "Too many wrong attempts.\nApplication will close."
                )
                self.root.destroy()
            else:
                self.status_var.set(
                    f"Wrong password. {remaining} attempt(s) remaining."
                )
                self.password_var.set("")

    def on_close(self):
        self.authenticated = False
        self.root.destroy()

    def run(self) -> bool:
        """Show login. Returns True if authenticated."""
        self.root.mainloop()
        return self.authenticated
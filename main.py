"""
Salary Manager — Entry Point
Run this file to start the application.
"""
import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tkinter as tk
from src.database import init_database
from ui.login import LoginWindow
from ui.main_window import MainWindow


def main():
    # Initialize database on startup
    init_database()

    # Show login window first
    login = LoginWindow()
    if not login.run():
        # User cancelled or failed login
        return

    # Login successful — launch main window
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
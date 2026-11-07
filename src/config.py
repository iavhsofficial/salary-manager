"""
Central configuration for Salary Manager.
All constants, paths, and settings live here.
"""
import os
import sys
from pathlib import Path

# ----------------------------------------
# Base directory logic
# - When running as script (python main.py): use project folder
# - When running as EXE (PyInstaller): use EXE's folder
# ----------------------------------------
if getattr(sys, "frozen", False):
    # Running as bundled EXE
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    # Running as script
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
PAYSLIP_DIR = BASE_DIR / "payslips"
LOGS_DIR = BASE_DIR / "logs"
BACKUP_DIR = BASE_DIR / "backups"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure directories exist
for _dir in (DATA_DIR, PAYSLIP_DIR, LOGS_DIR, ASSETS_DIR, BACKUP_DIR):
    _dir.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "salary.db"

# ============================================
# SCHOOL INFO
# ============================================
SCHOOL_NAME = "ISLAMIC ALTA VISTA HIGH SCHOOL"
PAYSLIP_TITLE = "STAFF PAY STATEMENT"
PAYSLIP_FOOTER = "This is a computer-generated payslip. No signature required."

# ============================================
# SALARY RULES
# ============================================
WORKING_DAYS_PER_MONTH = 30

# ============================================
# DEFAULTS
# ============================================
DEFAULT_MONTH = ""          # Empty — user must select
MONTH_PLACEHOLDER = "Select Month"
DEFAULT_YEAR = 2026

MONTHS = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]

# ============================================
# WHATSAPP CLOUD API
# (Will be loaded from env or config_secrets.json later)
# ============================================
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_API_VERSION = "v18.0"

# ============================================
# PAYSLIP FOLDER HELPERS
# ============================================
def get_payslip_dir(month, year):
    """
    Return the payslip folder for a specific month.
    Creates it if it doesn't exist.
    Example: payslips/August_2026/
    """
    folder = PAYSLIP_DIR / f"{month}_{year}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder
# ============================================
# SECURITY / PASSWORD
# ============================================
SECRETS_FILE = BASE_DIR / "config_secrets.json"
DEFAULT_PASSWORD = "iavhs2026"     # User can change later
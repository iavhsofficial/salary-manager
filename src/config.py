"""
Central configuration for Salary Manager.
All constants, paths, and settings live here.
"""
import os
from pathlib import Path

# ============================================
# PATHS
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PAYSLIP_DIR = BASE_DIR / "payslips"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"

# Ensure directories exist
for _dir in (DATA_DIR, PAYSLIP_DIR, LOGS_DIR, ASSETS_DIR):
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
DEFAULT_MONTH = "August"
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
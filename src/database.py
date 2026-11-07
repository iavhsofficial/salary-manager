"""
SQLite database layer for Salary Manager.
All DB operations go through this module.
"""
import sqlite3
from contextlib import contextmanager
from src.config import DB_PATH


@contextmanager
def get_connection():
    """Context manager for safe DB connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Create all tables if they don't exist."""
    with get_connection() as conn:
        c = conn.cursor()

        # ---- Staff table ----
        c.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sr_no INTEGER,
                name TEXT NOT NULL,
                date_of_joining TEXT,
                department TEXT,
                designation TEXT,
                basic_pay REAL DEFAULT 0,
                whatsapp TEXT,
                mobile TEXT,
                cnic TEXT,
                address TEXT,
                payment_mode TEXT DEFAULT 'Cash',
                bank_name TEXT,
                bank_account TEXT,
                security_total REAL DEFAULT 0,
                security_installments INTEGER DEFAULT 0,
                security_per_month REAL DEFAULT 0,
                security_already_deducted REAL DEFAULT 0,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---- Salary table ----
        c.execute("""
            CREATE TABLE IF NOT EXISTS salary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                writing REAL DEFAULT 0,
                speaking REAL DEFAULT 0,
                checking REAL DEFAULT 0,
                class_teacher REAL DEFAULT 0,
                coordination REAL DEFAULT 0,
                previous_pay REAL DEFAULT 0,
                increment REAL DEFAULT 0,
                overtime_allowance REAL DEFAULT 0,
                overtime_count REAL DEFAULT 0,
                overtime_type TEXT DEFAULT 'H',
                overtime_rate REAL DEFAULT 200,
                gross_pay REAL DEFAULT 0,
                total_earnings REAL DEFAULT 0,
                no_late_arrivals INTEGER DEFAULT 0,
                late_arrival_deduction REAL DEFAULT 0,
                no_short_leaves INTEGER DEFAULT 0,
                short_leave_deduction REAL DEFAULT 0,
                no_leaves INTEGER DEFAULT 0,
                leaves_deduction REAL DEFAULT 0,
                absentee_deduction REAL DEFAULT 0,
                no_absentees INTEGER DEFAULT 0,
                -- Fixed Deductions
                gp_fund REAL DEFAULT 0,
                social_security REAL DEFAULT 0,
                security_deduction REAL DEFAULT 0,
                oab REAL DEFAULT 0,
                apply_social_security INTEGER DEFAULT 0,
                apply_oab INTEGER DEFAULT 0,
                misc_allowance REAL DEFAULT 0,
                misc_deduction REAL DEFAULT 0,
                total_deductions REAL DEFAULT 0,
                net_pay REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff(id),
                UNIQUE(staff_id, month, year)
            )
        """)

        # ---- Indexes ----
        c.execute("CREATE INDEX IF NOT EXISTS idx_staff_name ON staff(name)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_salary_month ON salary(month, year)")

    print(f"Database initialized at {DB_PATH}")


# ============================================
# STAFF OPERATIONS
# ============================================
def add_staff(sr_no, name, date_of_joining, department, designation, basic_pay,
              whatsapp="", mobile="", cnic="", address="",
              payment_mode="Cash", bank_name="", bank_account="",
              security_total=0, security_installments=0,
              security_per_month=0, security_already_deducted=0):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO staff (
                sr_no, name, date_of_joining, department, designation, basic_pay,
                whatsapp, mobile, cnic, address, payment_mode, bank_name, bank_account,
                security_total, security_installments, security_per_month, security_already_deducted
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (sr_no, name, date_of_joining, department, designation, basic_pay,
              whatsapp, mobile, cnic, address, payment_mode, bank_name, bank_account,
              security_total, security_installments, security_per_month, security_already_deducted))
        new_id = c.lastrowid

    # Re-sequence after insert
    resequence_staff()
    return new_id


def get_all_staff(active_only=True, search=None):
    with get_connection() as conn:
        c = conn.cursor()
        query = "SELECT * FROM staff"
        params = []
        conditions = []
        if active_only:
            conditions.append("active = 1")
        if search:
            conditions.append("name LIKE ?")
            params.append(f"%{search}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY sr_no ASC"
        c.execute(query, params)
        return [dict(row) for row in c.fetchall()]


def get_staff(staff_id):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM staff WHERE id = ?", (staff_id,))
        row = c.fetchone()
        return dict(row) if row else None


def update_staff(staff_id, **fields):
    if not fields:
        return

    # Don't let sr_no be overwritten by editing
    # (sr_no is auto-managed by resequence_staff)
    fields.pop("sr_no", None)

    with get_connection() as conn:
        c = conn.cursor()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [staff_id]
        c.execute(f"UPDATE staff SET {set_clause} WHERE id = ?", values)

    # Re-sequence after update (in case order matters)
    resequence_staff()

def delete_staff(staff_id):
    """Soft delete — keep history. Then re-sequence remaining staff."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE staff SET active = 0 WHERE id = ?", (staff_id,))

    # Re-sequence remaining active staff
    resequence_staff()


# ============================================
# SALARY OPERATIONS
# ============================================
def save_salary(staff_id, month, year, data):
    """Insert or update salary record."""
    with get_connection() as conn:
        c = conn.cursor()

        c.execute(
            "SELECT id FROM salary WHERE staff_id=? AND month=? AND year=?",
            (staff_id, month, year)
        )
        existing = c.fetchone()

        fields = [
            'writing', 'speaking', 'checking',
            'class_teacher', 'coordination', 'previous_pay',
            'increment',
            'ot_hours', 'ot_days', 'overtime_rate', 'overtime_allowance', # Naye fields
            'gross_pay', 'total_earnings',
            'no_late_arrivals', 'late_arrival_deduction',
            'no_short_leaves', 'short_leave_deduction',
            'no_leaves', 'leaves_deduction',
            'no_absentees', 'absentee_deduction',
            'gp_fund', 'social_security', 'security_deduction',
            'oab', 'apply_security', 'apply_social_security', 'apply_oab',
            'misc_allowance', 'misc_deduction',
            'total_deductions', 'net_pay'
        ]

        if existing:
            set_clause = ", ".join(f"{f} = ?" for f in fields)
            values = [data.get(f, 0) for f in fields] + [existing["id"]]
            c.execute(f"UPDATE salary SET {set_clause} WHERE id = ?", values)
            return existing["id"]
        else:
            placeholders = ", ".join("?" * (3 + len(fields)))
            columns = "staff_id, month, year, " + ", ".join(fields)
            values = [staff_id, month, year] + [data.get(f, 0) for f in fields]
            c.execute(
                f"INSERT INTO salary ({columns}) VALUES ({placeholders})",
                values
            )
            return c.lastrowid


def get_salary(staff_id, month, year):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM salary WHERE staff_id=? AND month=? AND year=?",
            (staff_id, month, year)
        )
        row = c.fetchone()
        return dict(row) if row else None


def get_all_salaries_for_month(month, year):
    """Join staff + salary for a given month."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT
                s.id as staff_id, s.sr_no, s.name, s.date_of_joining,
                s.basic_pay, s.whatsapp, s.department, s.designation,
                s.payment_mode, s.bank_name, s.bank_account,
                s.security_total, s.security_installments,
                s.security_per_month, s.security_already_deducted,
                sal.writing, sal.speaking, sal.checking,
                sal.class_teacher, sal.coordination, sal.previous_pay,
                sal.increment,
                sal.overtime_count, sal.overtime_type,
                sal.overtime_rate, sal.overtime_allowance,
                sal.gross_pay, sal.total_earnings,
                sal.no_late_arrivals, sal.late_arrival_deduction,
                sal.no_short_leaves, sal.short_leave_deduction,
                sal.no_leaves, sal.leaves_deduction,
                sal.no_absentees, sal.absentee_deduction,
                sal.gp_fund, sal.social_security, sal.security_deduction,
                sal.oab, sal.apply_security, sal.apply_social_security, sal.apply_oab,
                sal.misc_allowance, sal.misc_deduction,
                sal.total_deductions, sal.net_pay
            FROM staff s
            LEFT JOIN salary sal ON s.id = sal.staff_id
                AND sal.month = ? AND sal.year = ?
            WHERE s.active = 1
            ORDER BY s.sr_no, s.name
        """, (month, year))
        return [dict(row) for row in c.fetchall()]


def update_security_deducted(staff_id, amount):
    """Add amount to staff's already_deducted security."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE staff SET security_already_deducted = "
            "COALESCE(security_already_deducted, 0) + ? WHERE id = ?",
            (amount, staff_id)
        )
def get_previous_salary(staff_id, current_month, current_year):
    """
    Find the most recent salary record BEFORE the given month/year.
    Used for auto-fill (carry-forward) in the Salary Dialog.
    Returns dict or None.
    """
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    try:
        current_month_idx = month_order.index(current_month)
    except ValueError:
        return None

    with get_connection() as conn:
        c = conn.cursor()

        # Look for salaries in earlier months of same year, then earlier years
        # Try to find the latest one
        c.execute("""
            SELECT * FROM salary
            WHERE staff_id = ?
            ORDER BY year DESC, id DESC
        """, (staff_id,))
        rows = c.fetchall()

        # Filter: find most recent record that is BEFORE current month/year
        best = None
        best_key = None
        for row in rows:
            r = dict(row)
            r_month = r.get("month")
            r_year = r.get("year")
            if r_month not in month_order:
                continue
            r_idx = month_order.index(r_month)
            # Compare: (year, month_idx)
            key = (r_year, r_idx)
            current_key = (current_year, current_month_idx)
            if key < current_key:
                if best_key is None or key > best_key:
                    best = r
                    best_key = key

        return best
def create_backup():
    """
    Create a timestamped backup of the database.
    Returns the backup file path.
    """
    import shutil
    from datetime import datetime
    from src.config import BACKUP_DIR, DB_PATH

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    backup_name = f"salary_backup_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_name

    shutil.copy2(DB_PATH, backup_path)
    return str(backup_path)


def list_backups():
    """Return list of backup files, newest first."""
    from src.config import BACKUP_DIR

    if not BACKUP_DIR.exists():
        return []

    backups = sorted(
        [f for f in BACKUP_DIR.iterdir() if f.suffix == ".db"],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return [str(f) for f in backups]
def auto_backup():
    """
    Create an auto-backup of the database (once per day).
    Deletes auto-backups older than 7 days.
    Returns the backup path or None if already done today.
    """
    import shutil
    from datetime import datetime, timedelta
    from src.config import BACKUP_DIR, DB_PATH

    if not DB_PATH.exists():
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    backup_name = f"auto_backup_{today}.db"
    backup_path = BACKUP_DIR / backup_name

    # Skip if today's auto-backup already exists
    if backup_path.exists():
        return None

    # Create backup
    try:
        shutil.copy2(DB_PATH, backup_path)
    except Exception as e:
        print(f"Auto-backup failed: {e}")
        return None

    # Cleanup old auto-backups (older than 7 days)
    try:
        cutoff = datetime.now() - timedelta(days=7)
        for f in BACKUP_DIR.iterdir():
            if f.name.startswith("auto_backup_") and f.suffix == ".db":
                # Extract date from filename: auto_backup_YYYY-MM-DD.db
                try:
                    date_part = f.stem.replace("auto_backup_", "")
                    file_date = datetime.strptime(date_part, "%Y-%m-%d")
                    if file_date < cutoff:
                        f.unlink()
                except (ValueError, OSError):
                    pass
    except Exception:
        pass

    return str(backup_path)
def get_next_sr_no():
    """Get the next available serial number (max + 1)."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT MAX(sr_no) FROM staff WHERE active = 1")
        result = c.fetchone()[0]
        if result is None:
            return 1
        return int(result) + 1
def resequence_staff():
    """
    Re-number all active staff sequentially (1, 2, 3, ...).
    Orders by id (insertion order) — so newest staff appear at the bottom.
    """
    with get_connection() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT id FROM staff WHERE active = 1 ORDER BY id ASC"
        )
        rows = c.fetchall()

        for idx, row in enumerate(rows, start=1):
            c.execute(
                "UPDATE staff SET sr_no = ? WHERE id = ?",
                (idx, row["id"])
            )
def get_staff_with_gross(search=None, department=None, sort_by="sr_no"):
    """
    Get all active staff + their LATEST gross pay from salary table.
    Supports search by name and filter by department.
    """
    with get_connection() as conn:
        c = conn.cursor()

        # Build WHERE clause
        where_clause = "WHERE s.active = 1"
        params = []
        
        if search:
            where_clause += " AND s.name LIKE ?"
            params.append(f"%{search}%")
            
        if department and department != "All":
            where_clause += " AND s.department = ?"
            params.append(department)

        # Query: staff + latest gross from salary
        query = f"""
            SELECT
                s.id, s.sr_no, s.name, s.date_of_joining,
                s.department, s.designation, s.basic_pay,
                s.payment_mode, s.whatsapp,
                (
                    SELECT sal.gross_pay
                    FROM salary sal
                    WHERE sal.staff_id = s.id
                    ORDER BY sal.year DESC, sal.id DESC
                    LIMIT 1
                ) AS latest_gross
            FROM staff s
            {where_clause}
            ORDER BY s.sr_no ASC
        """

        c.execute(query, params)
        # Fetch raw data
        c.execute(query, params)
        rows = [dict(row) for row in c.fetchall()]
        
        # ---- Apply Sorting ----
        if sort_by == "doj":
            # Parse date purely mathematically (integer comparison)
            # DD-MM-YY or DD-MM-YYYY -> returns (YYYY, MM, DD) tuple
            def parse_doj(r):
                doj_str = r.get("date_of_joining") or ""
                doj_str = doj_str.strip().replace("/", "-").replace(".", "-")
                parts = doj_str.split("-")
                
                if len(parts) == 3:
                    try:
                        d = int(parts[0])
                        m = int(parts[1])
                        y = int(parts[2])
                        # Fix 2-digit year (e.g., '21' becomes 2021, '99' becomes 1999)
                        if y < 100:
                            y = 2000 + y if y < 50 else 1900 + y
                        return (y, m, d)
                    except ValueError:
                        pass
                # Invalid/missing dates go to the bottom
                return (9999, 99, 99)
            
            rows.sort(key=parse_doj)
            
        elif sort_by == "department":
            rows.sort(key=lambda r: (
                (r.get("department") or "ZZZ").upper(),
                r.get("sr_no") or 0
            ))
        else:
            rows.sort(key=lambda r: r.get("sr_no") or 0)
            
        return rows
        return [dict(row) for row in c.fetchall()]


def get_all_departments():
    """Get a unique list of all departments for the dropdown."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT DISTINCT department FROM staff WHERE active = 1 AND department != '' ORDER BY department ASC")
        return [row[0] for row in c.fetchall()]

def import_combined_data_from_excel(rows):
    """
    Import Staff details AND their Monthly Salary from Excel rows.
    Updates existing records, adds new ones.
    """
    from src.calculations import calculate_salary
    from src import app_settings

    added_staff = 0
    added_salary = 0
    updated_salary = 0
    errors = []

    for i, row in enumerate(rows, start=1):
        name = str(row.get("Name") or "").strip()
        if not name:
            continue

        # --- 1. STAFF DATA ---
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, department, payment_mode, whatsapp, security_total, security_installments, security_per_month FROM staff WHERE LOWER(name) = LOWER(?)", (name,))
            existing_staff = c.fetchone()

        is_new = existing_staff is None

        # Defaults agar data missing ho
        sr_no = int(row.get("Sr #") or 0) if str(row.get("Sr #")).strip() else 0
        dept = str(row.get("Department") or "").strip().upper()
        if not dept and existing_staff: dept = existing_staff["department"]
        if not dept: dept = "UNASSIGNED"

        designation = str(row.get("Designation") or "").strip()
        basic_pay = float(row.get("Basic Pay") or 0)
        doj = str(row.get("DOJ") or "").strip()
        
        whatsapp = str(row.get("WhatsApp") or "").strip()
        if not whatsapp and existing_staff: whatsapp = existing_staff["whatsapp"]
        
        payment_mode = str(row.get("Payment Mode") or "").strip().title()
        if not payment_mode and existing_staff: payment_mode = existing_staff["payment_mode"]
        if not payment_mode: payment_mode = "Cash"

        bank_name = str(row.get("Account Holder Name") or "").strip()
        bank_acc = str(row.get("Bank Account") or "").strip()

        sec_total = float(row.get("Security Total") or 0)
        if not sec_total and existing_staff: sec_total = existing_staff["security_total"]
        sec_inst = int(row.get("Security Installments") or 0)
        if not sec_inst and existing_staff: sec_inst = existing_staff["security_installments"]
        sec_pm = float(row.get("Security Per Month") or 0)
        if not sec_pm and existing_staff: sec_pm = existing_staff["security_per_month"]
        sec_already = float(row.get("Security Already Deducted") or 0)

        staff_data = {
            "sr_no": sr_no, "name": name, "date_of_joining": doj,
            "department": dept, "designation": designation, "basic_pay": basic_pay,
            "whatsapp": whatsapp, "payment_mode": payment_mode,
            "bank_name": bank_name, "bank_account": bank_acc,
            "security_total": sec_total, "security_installments": sec_inst,
            "security_per_month": sec_pm, "security_already_deducted": sec_already
        }

        staff_id = None
        with get_connection() as conn:
            c = conn.cursor()
            if is_new:
                columns = ", ".join(staff_data.keys())
                placeholders = ", ".join("?" * len(staff_data))
                c.execute(f"INSERT INTO staff ({columns}) VALUES ({placeholders})", list(staff_data.values()))
                staff_id = c.lastrowid
                added_staff += 1
            else:
                staff_id = existing_staff["id"]
                set_clause = ", ".join(f"{k} = ?" for k in staff_data)
                c.execute(f"UPDATE staff SET {set_clause} WHERE id = ?", list(staff_data.values()) + [staff_id])

        # --- 2. SALARY DATA ---
        month = str(row.get("Month") or "").strip().title()
        try:
            year = int(row.get("Year") or 0)
        except ValueError:
            year = 0

        if not month or not year:
            continue # Agar month/year nahi hai toh salary skip karega

        # Auto check SS and OAB if amount/yes is written in Excel
        apply_ss = 1 if str(row.get("Apply Social Security") or row.get("Social Security") or "").strip().lower() in ("1", "yes", "true", "check") else 0
        apply_oab = 1 if str(row.get("Apply OAB") or row.get("OAB") or "").strip().lower() in ("1", "yes", "true", "check") else 0

        inputs = {
            "writing": float(row.get("Writing") or 0),
            "speaking": float(row.get("Speaking") or 0),
            "checking": float(row.get("Checking") or 0),
            "class_teacher": float(row.get("Class Teacher") or 0),
            "coordination": float(row.get("Coordination") or 0),
            "previous_pay": float(row.get("Previous Pay") or 0),
            "increment": float(row.get("Increment") or 0),
            "overtime_count": float(row.get("Overtime Count") or 0),
            "overtime_type": str(row.get("Overtime Type") or "H").strip().upper(),
            "no_late_arrivals": int(row.get("No. of Late Arrivals") or 0),
            "no_short_leaves": int(row.get("No. of Short Leaves") or 0),
            "no_leaves": int(row.get("No. of Leaves") or 0),
            "no_absentees": int(row.get("No. of Absentees") or 0),
            "apply_social_security": apply_ss,
            "apply_oab": apply_oab,
            "apply_security": 1 if sec_pm > 0 else 0,
            "security_deduction": sec_pm if sec_pm > 0 else 0,
        }

        result = calculate_salary(basic_pay, inputs)

        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM salary WHERE staff_id=? AND month=? AND year=?", (staff_id, month, year))
            existing_sal = c.fetchone()

            fields = list(result.keys())
            if existing_sal:
                sal_id = existing_sal["id"]
                set_clause = ", ".join(f"{f} = ?" for f in fields)
                c.execute(f"UPDATE salary SET {set_clause} WHERE id = ?", [result.get(f) for f in fields] + [sal_id])
                updated_salary += 1
            else:
                columns = "staff_id, month, year, " + ", ".join(fields)
                placeholders = ", ".join("?" * (3 + len(fields)))
                values = [staff_id, month, year] + [result.get(f) for f in fields]
                c.execute(f"INSERT INTO salary ({columns}) VALUES ({placeholders})", values)
                added_salary += 1

    resequence_staff()
    return added_staff, added_salary, updated_salary
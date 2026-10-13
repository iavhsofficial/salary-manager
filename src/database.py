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
                doj TEXT,
                department TEXT,
                designation TEXT,
                basic_pay REAL DEFAULT 0,
                whatsapp TEXT,
                bank_account TEXT,
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
                dis REAL DEFAULT 0,
                ct REAL DEFAULT 0,
                od REAL DEFAULT 0,
                ot_extra REAL DEFAULT 0,
                e_day REAL DEFAULT 0,
                la_adv REAL DEFAULT 0,
                gp_fund REAL DEFAULT 0,
                sec REAL DEFAULT 0,
                s_sec REAL DEFAULT 0,
                oab REAL DEFAULT 0,
                sl REAL DEFAULT 0,
                cl_day REAL DEFAULT 0,
                ann_l REAL DEFAULT 0,
                ab_fine REAL DEFAULT 0,
                gross_pay REAL DEFAULT 0,
                total_ded REAL DEFAULT 0,
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
def add_staff(sr_no, name, doj, department, designation,
              basic_pay, whatsapp, bank_account=""):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO staff (sr_no, name, doj, department, designation,
                               basic_pay, whatsapp, bank_account)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sr_no, name, doj, department, designation,
              basic_pay, whatsapp, bank_account))
        return c.lastrowid


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
        query += " ORDER BY sr_no, name"
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
    with get_connection() as conn:
        c = conn.cursor()
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [staff_id]
        c.execute(f"UPDATE staff SET {set_clause} WHERE id = ?", values)


def delete_staff(staff_id):
    """Soft delete — keep history."""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("UPDATE staff SET active = 0 WHERE id = ?", (staff_id,))


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
            'writing', 'speaking', 'checking', 'dis', 'ct', 'od',
            'ot_extra', 'e_day', 'la_adv', 'gp_fund', 'sec', 's_sec',
            'oab', 'sl', 'cl_day', 'ann_l', 'ab_fine',
            'gross_pay', 'total_ded', 'net_pay'
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
            SELECT s.id as staff_id, s.sr_no, s.name, s.doj, s.basic_pay,
                   s.whatsapp, s.department, s.designation,
                   sal.writing, sal.speaking, sal.checking, sal.dis, sal.ct,
                   sal.od, sal.ot_extra, sal.e_day, sal.la_adv, sal.gp_fund,
                   sal.sec, sal.s_sec, sal.oab, sal.sl, sal.cl_day, sal.ann_l,
                   sal.ab_fine, sal.gross_pay, sal.total_ded, sal.net_pay
            FROM staff s
            LEFT JOIN salary sal ON s.id = sal.staff_id
                AND sal.month = ? AND sal.year = ?
            WHERE s.active = 1
            ORDER BY s.sr_no, s.name
        """, (month, year))
        return [dict(row) for row in c.fetchall()]
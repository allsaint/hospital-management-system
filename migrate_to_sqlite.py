"""
migrate_to_sqlite.py
--------------------
Migrates ALL tables from the hospital PostgreSQL database to a local SQLite file.
Tables covered (23):
  admin_users, cashier_users, admin_audit_logs, pharmacists, billing_users,
  drugs, drug_sales, receipts, receipt_items, stock_movements,
  billing_invoice, billing_receipt, payments, users,
  hr_users, departments, staff, attendance, leaves,
  schedules, payroll, documents, shift_swap_requests

Usage:
  python migrate_to_sqlite.py
  python migrate_to_sqlite.py --pg-url postgresql://user:pass@host:5432/dbname
  python migrate_to_sqlite.py --fresh   (skip PostgreSQL copy, create empty DB with default users only)
"""

import sqlite3
import argparse
import sys
import os
from datetime import datetime

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────
DEFAULT_PG_URL = "postgresql://flask_user:Olarewaju1.@localhost:5432/hospital2_db"
SQLITE_FILE = "hospital.db"

# ──────────────────────────────────────────────
# SQLite SCHEMA  (all 23 tables)
# ──────────────────────────────────────────────
SCHEMA = """
-- ── USER / AUTH TABLES ──────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS admin_users (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    username          TEXT UNIQUE NOT NULL,
    password          TEXT NOT NULL,
    full_name         TEXT,
    email             TEXT,
    role              TEXT DEFAULT 'Admin',
    is_super_admin    INTEGER DEFAULT 0,
    is_active         INTEGER DEFAULT 1,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by        INTEGER,
    last_login        TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cashier_users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    full_name   TEXT,
    email       TEXT,
    is_active   INTEGER DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by  INTEGER,
    last_login  TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pharmacists (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    full_name   TEXT,
    is_active   INTEGER DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by  INTEGER
);

CREATE TABLE IF NOT EXISTS billing_users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    full_name   TEXT,
    is_active   INTEGER DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by  INTEGER
);

CREATE TABLE IF NOT EXISTS hr_users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    full_name   TEXT NOT NULL,
    email       TEXT,
    role        TEXT DEFAULT 'HR Staff',
    is_active   INTEGER DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── AUDIT ────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id    INTEGER,
    action      TEXT NOT NULL,
    details     TEXT,
    ip_address  TEXT,
    user_agent  TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── PHARMACY TABLES ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS drugs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    strength            TEXT NOT NULL,
    unit_price          REAL NOT NULL,
    stock_quantity      INTEGER NOT NULL,
    expiry_date         DATE NOT NULL,
    low_stock_threshold INTEGER DEFAULT 20,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drug_sales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_no      TEXT UNIQUE NOT NULL,
    patient_name    TEXT,
    patient_id      TEXT,
    items           TEXT NOT NULL,
    subtotal        REAL NOT NULL,
    discount        REAL DEFAULT 0.00,
    tax             REAL DEFAULT 0.00,
    grand_total     REAL NOT NULL,
    pharmacist      TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS receipts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name    TEXT,
    patient_id      TEXT,
    subtotal        REAL NOT NULL,
    discount        REAL DEFAULT 0.00,
    tax             REAL DEFAULT 0.00,
    total_amount    REAL NOT NULL,
    grand_total     REAL NOT NULL,
    pharmacist      TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS receipt_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id  INTEGER NOT NULL,
    drug_name   TEXT NOT NULL,
    strength    TEXT NOT NULL,
    quantity    INTEGER NOT NULL,
    unit_price  REAL NOT NULL,
    FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id         INTEGER NOT NULL,
    movement_type   TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    note            TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (drug_id) REFERENCES drugs(id) ON DELETE CASCADE
);

-- ── BILLING TABLES ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS billing_invoice (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name    TEXT NOT NULL,
    service_type    TEXT NOT NULL,
    amount          REAL NOT NULL,
    status          TEXT DEFAULT 'UNPAID',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS billing_receipt (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id      INTEGER NOT NULL,
    amount_paid     REAL NOT NULL,
    payment_method  TEXT NOT NULL,
    received_by     TEXT NOT NULL,
    payment_date    TIMESTAMP NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES billing_invoice(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name    TEXT NOT NULL,
    service_type    TEXT NOT NULL,
    subtotal        REAL NOT NULL,
    discount        REAL DEFAULT 0.00,
    tax             REAL DEFAULT 0.00,
    grand_total     REAL NOT NULL,
    amount_paid     REAL NOT NULL,
    balance         REAL NOT NULL,
    payment_method  TEXT NOT NULL,
    status          TEXT NOT NULL,
    payment_date    DATE NOT NULL,
    recorded_by     INTEGER NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── HR TABLES ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS departments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    code            TEXT UNIQUE NOT NULL,
    description     TEXT,
    head_of_dept    TEXT,
    status          TEXT DEFAULT 'Active',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staff (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id            TEXT UNIQUE NOT NULL,
    first_name          TEXT NOT NULL,
    last_name           TEXT NOT NULL,
    department_id       INTEGER,
    position            TEXT NOT NULL,
    employment_type     TEXT,
    email               TEXT,
    phone               TEXT,
    hire_date           DATE NOT NULL,
    salary              REAL,
    status              TEXT DEFAULT 'Active',
    emergency_contact   TEXT,
    address             TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id    INTEGER,
    date        DATE NOT NULL,
    check_in    TIME,
    check_out   TIME,
    status      TEXT,
    remarks     TEXT,
    recorded_by INTEGER,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(staff_id, date),
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS leaves (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id        INTEGER,
    leave_type      TEXT NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    days_requested  INTEGER NOT NULL,
    reason          TEXT,
    status          TEXT DEFAULT 'Pending',
    approved_by     INTEGER,
    approved_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS schedules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id        INTEGER,
    schedule_date   DATE NOT NULL,
    shift_type      TEXT,
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    location        TEXT,
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payroll (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id        INTEGER,
    pay_period      TEXT,
    basic_salary    REAL,
    allowances      REAL,
    deductions      REAL,
    net_salary      REAL,
    status          TEXT DEFAULT 'Pending',
    payment_date    DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_id        INTEGER,
    document_type   TEXT,
    document_name   TEXT,
    file_path       TEXT,
    uploaded_by     INTEGER,
    uploaded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shift_swap_requests (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id     INTEGER NOT NULL,
    from_staff_id   INTEGER NOT NULL,
    to_staff_id     INTEGER NOT NULL,
    reason          TEXT,
    status          TEXT DEFAULT 'Pending',
    requested_by    INTEGER,
    requested_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by     INTEGER,
    approved_at     TIMESTAMP,
    reviewed_by     INTEGER,
    reviewed_at     TIMESTAMP,
    rejection_reason TEXT,
    FOREIGN KEY (schedule_id)   REFERENCES schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (from_staff_id) REFERENCES staff(id) ON DELETE CASCADE,
    FOREIGN KEY (to_staff_id)   REFERENCES staff(id) ON DELETE CASCADE
);
"""

# ──────────────────────────────────────────────
# TABLE COPY SPECS
# Each entry: (pg_table, sqlite_table, pg_columns, sqlite_placeholders)
# pg_columns excludes id (autoincrement handled by SQLite)
# ──────────────────────────────────────────────
TABLE_SPECS = [
    # (pg_table, columns_to_copy)
    ("admin_users",        "username, password, full_name, email, role, is_super_admin, is_active, created_at, created_by, last_login"),
    ("cashier_users",      "username, password, full_name, email, is_active, created_at, created_by, last_login"),
    ("pharmacists",        "username, password, full_name, is_active, created_at, created_by"),
    ("billing_users",      "username, password, full_name, is_active, created_at, created_by"),
    ("hr_users",           "username, password, full_name, email, role, is_active, created_at"),
    ("users",              "username, password, created_at"),
    ("admin_audit_logs",   "admin_id, action, details, ip_address, user_agent, created_at"),
    ("drugs",              "name, strength, unit_price, stock_quantity, expiry_date, low_stock_threshold, created_at, updated_at"),
    ("drug_sales",         "receipt_no, patient_name, patient_id, items, subtotal, discount, tax, grand_total, pharmacist, created_at"),
    ("receipts",           "patient_name, patient_id, subtotal, discount, tax, total_amount, grand_total, pharmacist, created_at"),
    ("receipt_items",      "receipt_id, drug_name, strength, quantity, unit_price"),
    ("stock_movements",    "drug_id, movement_type, quantity, user_id, note, created_at"),
    ("billing_invoice",    "patient_name, service_type, amount, status, created_at"),
    ("billing_receipt",    "invoice_id, amount_paid, payment_method, received_by, payment_date"),
    ("payments",           "patient_name, service_type, subtotal, discount, tax, grand_total, amount_paid, balance, payment_method, status, payment_date, recorded_by, created_at"),
    ("departments",        "name, code, description, head_of_dept, status, created_at"),
    ("staff",              "staff_id, first_name, last_name, department_id, position, employment_type, email, phone, hire_date, salary, status, emergency_contact, address, created_at, updated_at"),
    ("attendance",         "staff_id, date, check_in, check_out, status, remarks, recorded_by, created_at"),
    ("leaves",             "staff_id, leave_type, start_date, end_date, days_requested, reason, status, approved_by, approved_at, created_at"),
    ("schedules",          "staff_id, schedule_date, shift_type, start_time, end_time, location, notes, created_at"),
    ("payroll",            "staff_id, pay_period, basic_salary, allowances, deductions, net_salary, status, payment_date, created_at"),
    ("documents",          "staff_id, document_type, document_name, file_path, uploaded_by, uploaded_at"),
    ("shift_swap_requests","schedule_id, from_staff_id, to_staff_id, reason, status, requested_by, requested_at, approved_by, approved_at, reviewed_by, reviewed_at, rejection_reason"),
]


def create_sqlite_schema(sqlite_conn):
    print("Creating SQLite schema...")
    sqlite_conn.executescript(SCHEMA)
    sqlite_conn.commit()
    print("  ✔ All 23 tables created.\n")


def insert_default_users(sqlite_conn):
    """Insert default admin, pharmacist, and billing users."""
    try:
        from werkzeug.security import generate_password_hash
    except ImportError:
        print("  ⚠ werkzeug not installed — skipping default users. Run: pip install werkzeug")
        return

    defaults = [
        ("admin_users",   "admin",        "admin123",   "Super Admin", True),
        ("pharmacists",   "pharmacist1",  "pharma123",  "Pharmacist One", False),
        ("billing_users", "billing1",     "billing123", "Billing One", False),
    ]

    cursor = sqlite_conn.cursor()
    for table, username, raw_pw, full_name, is_super in defaults:
        hashed = generate_password_hash(raw_pw)
        if table == "admin_users":
            cursor.execute(
                f"INSERT OR IGNORE INTO {table} (username, password, full_name, is_super_admin) VALUES (?, ?, ?, ?)",
                (username, hashed, full_name, 1 if is_super else 0)
            )
        else:
            cursor.execute(
                f"INSERT OR IGNORE INTO {table} (username, password, full_name) VALUES (?, ?, ?)",
                (username, hashed, full_name)
            )
    sqlite_conn.commit()
    print("  ✔ Default users inserted (admin / pharmacist1 / billing1).\n")


def copy_from_postgres(pg_url, sqlite_conn):
    try:
        import psycopg2
    except ImportError:
        print("  ✗ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False

    print(f"Connecting to PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(pg_url)
        pg_cursor = pg_conn.cursor()
        print("  ✔ Connected.\n")
    except Exception as e:
        print(f"  ✗ Could not connect to PostgreSQL: {e}")
        return False

    sqlite_cursor = sqlite_conn.cursor()
    total_copied = 0

    for pg_table, columns in TABLE_SPECS:
        col_list = [c.strip() for c in columns.split(",")]
        placeholders = ", ".join(["?" for _ in col_list])

        # Check if PostgreSQL table exists
        pg_cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name=%s)",
            (pg_table,)
        )
        exists = pg_cursor.fetchone()[0]
        if not exists:
            print(f"  ⚠ Table '{pg_table}' not found in PostgreSQL — skipping.")
            continue

        # Check for missing columns gracefully
        pg_cursor.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name=%s",
            (pg_table,)
        )
        pg_cols = {row[0] for row in pg_cursor.fetchall()}
        safe_cols = [c for c in col_list if c in pg_cols]

        if not safe_cols:
            print(f"  ⚠ No matching columns for '{pg_table}' — skipping.")
            continue

        safe_col_str = ", ".join(safe_cols)
        safe_placeholders = ", ".join(["?" for _ in safe_cols])

        try:
            pg_cursor.execute(f"SELECT {safe_col_str} FROM {pg_table}")
            rows = pg_cursor.fetchall()

            # Convert rows: stringify JSONB/dict, cast booleans to int for SQLite
            converted = []
            for row in rows:
                new_row = []
                for val in row:
                    if isinstance(val, dict):
                        import json
                        new_row.append(json.dumps(val))
                    elif isinstance(val, bool):
                        new_row.append(1 if val else 0)
                    else:
                        new_row.append(val)
                converted.append(tuple(new_row))

            sqlite_cursor.executemany(
                f"INSERT OR IGNORE INTO {pg_table} ({safe_col_str}) VALUES ({safe_placeholders})",
                converted
            )
            sqlite_conn.commit()
            count = len(rows)
            total_copied += count
            print(f"  ✔ {pg_table:<25} → {count} rows copied.")
        except Exception as e:
            sqlite_conn.rollback()
            print(f"  ✗ Error copying '{pg_table}': {e}")

    pg_cursor.close()
    pg_conn.close()
    print(f"\n  Total rows copied: {total_copied}")
    return True


def verify(sqlite_conn):
    print("\n── Verification ─────────────────────────────────────")
    cursor = sqlite_conn.cursor()
    for pg_table, _ in TABLE_SPECS:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {pg_table}")
            count = cursor.fetchone()[0]
            print(f"  {pg_table:<30} {count:>6} rows")
        except Exception as e:
            print(f"  {pg_table:<30} ERROR: {e}")
    print("─────────────────────────────────────────────────────\n")


def main():
    parser = argparse.ArgumentParser(description="Migrate PostgreSQL → SQLite for hospital system")
    parser.add_argument("--pg-url",  default=DEFAULT_PG_URL, help="PostgreSQL connection URL")
    parser.add_argument("--out",     default=SQLITE_FILE,    help="Output SQLite file path")
    parser.add_argument("--fresh",   action="store_true",    help="Skip PostgreSQL copy, create empty DB only")
    args = parser.parse_args()

    print("=" * 55)
    print("  Hospital System — PostgreSQL → SQLite Migration")
    print("=" * 55)
    print(f"  Output file : {args.out}")
    print(f"  Mode        : {'fresh (no data copy)' if args.fresh else 'full migration'}")
    print()

    sqlite_conn = sqlite3.connect(args.out)
    sqlite_conn.execute("PRAGMA foreign_keys = ON")
    sqlite_conn.execute("PRAGMA journal_mode = WAL")

    create_sqlite_schema(sqlite_conn)

    if not args.fresh:
        success = copy_from_postgres(args.pg_url, sqlite_conn)
        if not success:
            print("\nPostgreSQL copy failed. Falling back to empty DB with default users.\n")

    print("Inserting default users...")
    insert_default_users(sqlite_conn)
    verify(sqlite_conn)

    sqlite_conn.close()
    print(f"✅ Done! SQLite database saved to: {args.out}")


if __name__ == "__main__":
    main()

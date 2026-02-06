# simple_migration.py
import psycopg2
import sqlite3
import json

def simple_migration():
    print("Creating SQLite database with essential tables...")
    
    # Create SQLite connection and tables
    sqlite_conn = sqlite3.connect('hospital.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # Only create essential tables for now
    essential_tables = {
        "drugs": """
            CREATE TABLE IF NOT EXISTS drugs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                strength TEXT NOT NULL,
                unit_price REAL NOT NULL,
                stock_quantity INTEGER NOT NULL,
                expiry_date DATE NOT NULL,
                low_stock_threshold INTEGER DEFAULT 20,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "receipts": """
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT,
                patient_id TEXT,
                subtotal REAL NOT NULL,
                discount REAL DEFAULT 0.00,
                tax REAL DEFAULT 0.00,
                total_amount REAL NOT NULL,
                grand_total REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "payments": """
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                service_type TEXT NOT NULL,
                subtotal REAL NOT NULL,
                discount REAL DEFAULT 0.00,
                tax REAL DEFAULT 0.00,
                grand_total REAL NOT NULL,
                amount_paid REAL NOT NULL,
                balance REAL NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL,
                payment_date DATE NOT NULL,
                recorded_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "users": """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
    }
    
    # Create tables
    for table_name, create_query in essential_tables.items():
        print(f"Creating {table_name} table...")
        sqlite_cursor.execute(create_query)
    
    sqlite_conn.commit()
    print("Essential tables created!")
    
    # Now try to copy data from PostgreSQL
    try:
        pg_conn = psycopg2.connect('postgresql://flask_user:Olarewaju1.@localhost:5432/all_saint_db')
        pg_cursor = pg_conn.cursor()
        print("Connected to PostgreSQL")
        
        # Copy drugs table
        print("\nCopying drugs...")
        pg_cursor.execute("SELECT * FROM drugs")
        drugs = pg_cursor.fetchall()
        for drug in drugs:
            sqlite_cursor.execute("""
                INSERT INTO drugs (name, strength, unit_price, stock_quantity, expiry_date, low_stock_threshold)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (drug[1], drug[2], drug[3], drug[4], drug[5], drug[6]))
        
        # Copy receipts
        print("Copying receipts...")
        pg_cursor.execute("SELECT * FROM receipts")
        receipts = pg_cursor.fetchall()
        for receipt in receipts:
            sqlite_cursor.execute("""
                INSERT INTO receipts (patient_name, patient_id, subtotal, discount, tax, total_amount, grand_total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (receipt[1], receipt[2], receipt[3], receipt[4], receipt[5], receipt[6], receipt[7]))
        
        # Copy payments
        print("Copying payments...")
        pg_cursor.execute("SELECT * FROM payments")
        payments = pg_cursor.fetchall()
        for payment in payments:
            sqlite_cursor.execute("""
                INSERT INTO payments (patient_name, service_type, subtotal, discount, tax, grand_total, 
                                     amount_paid, balance, payment_method, status, payment_date, recorded_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (payment[1], payment[2], payment[3], payment[4], payment[5], payment[6], 
                  payment[7], payment[8], payment[9], payment[10], payment[11], payment[12]))
        
        # Insert default users
        print("Creating default users...")
        from werkzeug.security import generate_password_hash
        default_users = [
            ('admin', generate_password_hash('admin123')),
            ('pharmacist1', generate_password_hash('pharma123')),
            ('billing1', generate_password_hash('billing123'))
        ]
        for username, password in default_users:
            sqlite_cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", 
                                (username, password))
        
        sqlite_conn.commit()
        print("\nMigration completed successfully!")
        
        pg_cursor.close()
        pg_conn.close()
        
    except Exception as e:
        print(f"Could not copy from PostgreSQL: {e}")
        print("Creating fresh database with default data only...")
    
    sqlite_cursor.close()
    sqlite_conn.close()
    print("\nSQLite database ready: hospital.db")

if __name__ == "__main__":
    simple_migration()
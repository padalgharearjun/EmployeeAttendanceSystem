# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect("data/database.db")
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT UNIQUE,
        name TEXT,
        password_hash TEXT,
        role TEXT,
        manager_id TEXT
    )''')

    # Attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT,
        log_in_date TEXT,
        log_in_time TEXT,
        log_out_date TEXT,
        log_out_time TEXT
    )''')

    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # Initialize last employee number if not exists
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('last_emp_number', 'EMP000000')")

    conn.commit()
    conn.close()

import sqlite3
import pandas as pd

def get_next_employee_number():
    conn = sqlite3.connect("data/database.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='last_emp_number'")
    last_number = c.fetchone()[0]
    next_number = int(last_number.replace('EMP', '')) + 1
    new_emp_id = f"EMP{next_number:06d}"
    c.execute("UPDATE settings SET value=? WHERE key='last_emp_number'", (new_emp_id,))
    conn.commit()
    conn.close()
    return new_emp_id

def create_user_auto(name, hashed_pw, role, manager_id=None):
    emp_id = get_next_employee_number()
    conn = sqlite3.connect("data/database.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (employee_id, name, password_hash, role, manager_id) VALUES (?, ?, ?, ?, ?)", 
              (emp_id, name, hashed_pw, role, manager_id))
    conn.commit()
    conn.close()
    return emp_id

def get_mapped_employees(manager_id):
    conn = sqlite3.connect("data/database.db")
    c = conn.cursor()
    c.execute("SELECT employee_id, name FROM users WHERE manager_id = ?", (manager_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def insert_attendance_from_csv(csv_file):
    df = pd.read_csv(csv_file)
    conn = sqlite3.connect("data/database.db")
    df.to_sql('attendance', conn, if_exists='append', index=False)
    conn.close()

def get_attendance(emp_id):
    conn = sqlite3.connect("data/database.db")
    df = pd.read_sql_query("SELECT * FROM attendance WHERE employee_id = ?", conn, params=(emp_id,))
    conn.close()
    return df

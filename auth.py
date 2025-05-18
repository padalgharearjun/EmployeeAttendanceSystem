import sqlite3
import bcrypt

def login_user(emp_id, password):
    conn = sqlite3.connect("data/database.db")
    c = conn.cursor()
    c.execute("SELECT password_hash, role, name FROM users WHERE employee_id = ?", (emp_id,))
    data = c.fetchone()
    conn.close()
    if data and bcrypt.checkpw(password.encode(), data[0].encode()):
        return True, data[1], data[2]  # success, role, name
    return False, None, None

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

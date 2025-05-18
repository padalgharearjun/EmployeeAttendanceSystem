# create_admin.py
from database import init_db
from auth import hash_password
import sqlite3

# Initialize database
init_db()

# Create admin user
conn = sqlite3.connect("data/database.db")
c = conn.cursor()

admin_id = "admin"
admin_name = "Admin User"
admin_password = "admin123"
hashed_pw = hash_password(admin_password)

c.execute("INSERT OR IGNORE INTO users (employee_id, name, password_hash, role) VALUES (?, ?, ?, ?)",
          (admin_id, admin_name, hashed_pw, "Admin"))

conn.commit()
conn.close()

print("✅ Admin user created.\nLogin credentials:")
print(f"Employee ID: {admin_id}")
print(f"Password: {admin_password}")

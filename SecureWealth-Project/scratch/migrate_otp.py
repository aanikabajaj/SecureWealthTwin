import sqlite3
import os

db_path = "securewealth_dev.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN otp_code VARCHAR(6)")
        print("Added otp_code column")
    except sqlite3.OperationalError as e:
        print(f"otp_code info: {e}")
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN otp_expiry DATETIME")
        print("Added otp_expiry column")
    except sqlite3.OperationalError as e:
        print(f"otp_expiry info: {e}")
        
    conn.commit()
    conn.close()
    print("Database sync complete.")
else:
    print(f"Database not found at {db_path}")

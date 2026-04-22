import sqlite3
import os

db_paths = ["backend/securewealth_dev.db", "securewealth_dev.db"]

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"Syncing {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login DATETIME")
            print("Added last_login column")
        except sqlite3.OperationalError as e:
            print(f"last_login info: {e}")
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN active_devices_count INTEGER DEFAULT 1")
            print("Added active_devices_count column")
        except sqlite3.OperationalError as e:
            print(f"active_devices_count info: {e}")
            
        conn.commit()
        conn.close()
        print(f"Database sync complete for {db_path}.")
    else:
        print(f"Database not found at {db_path}")

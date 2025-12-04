import sqlite3
import json

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM capstone_history")
rows = cursor.fetchall()

data = []
for row in rows:
    data.append({
        "id": row[0],
        "user_id": row[1],
        "title": row[2],
        "file_path": row[3],
        "created_at": row[4],
    })

with open("capstone_export.json", "w") as f:
    json.dump(data, f, indent=4)

print("Export completed! -> capstone_export.json")

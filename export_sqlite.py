import sqlite3
import json

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Export USERS table (modify if you have more tables)
cursor.execute("SELECT * FROM user")
columns = [col[0] for col in cursor.description]
data = [dict(zip(columns, row)) for row in cursor.fetchall()]

with open("users_export.json", "w") as f:
    json.dump(data, f, indent=4)

print("Exported to users_export.json")

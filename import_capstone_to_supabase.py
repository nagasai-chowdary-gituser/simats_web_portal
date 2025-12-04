from app import app, db, CapstoneHistory
import json
from datetime import datetime

with app.app_context():
    with open("capstone_export.json", "r") as f:
        data = json.load(f)

    for row in data:

        created = row.get("created_at")

        # FIX: Replace NULL with a safe fallback timestamp
        if created is None or created == "" or created == "null":
            created = datetime.utcnow().isoformat()

        record = CapstoneHistory(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            file_path=row["file_path"],
            created_at=created
        )

        db.session.add(record)

    try:
        db.session.commit()
        print("✅ Capstone migration completed!")
    except Exception as e:
        print("❌ Error:", e)
        db.session.rollback()

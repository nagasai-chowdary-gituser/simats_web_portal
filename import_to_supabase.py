import json
from app import db, User, app

with app.app_context():
    with open("users_export.json", "r") as f:
        users = json.load(f)

    for u in users:
        new_user = User(
            id=u["id"],
            username=u["username"],
            email=u["email"],
            reg_number=u.get("reg_number"),
            password=u["password"],   # already hashed
            is_admin=u.get("is_admin", False),
            security_bike=u.get("security_bike")
        )
        db.session.merge(new_user)  # merge = insert or update safely

    db.session.commit()

print("✅ Migration completed!")

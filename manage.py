from app import create_app, db
from app.models import AdminUser

app = create_app()
with app.app_context():
    kt = "000000-0000"  # change me
    if not AdminUser.query.filter_by(kennitala=kt).first():
        db.session.add(AdminUser(kennitala=kt))
        db.session.commit()
        print("Admin added:", kt)
    else:
        print("Admin already exists:", kt)

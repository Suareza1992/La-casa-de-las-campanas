"""
Run once to create the initial admin account.
  python seed.py
Then change the password immediately after first login.
"""
from models import SessionLocal, User

db = SessionLocal()
if db.query(User).filter_by(role='admin').first():
    print("Admin already exists — nothing to do.")
else:
    admin = User(username='Admin', email='casacampanaspr@gmail.com', role='admin')
    admin.set_password('admin123')
    db.add(admin)
    db.commit()
    print("✓ Admin created:")
    print("  Email:    casacampanaspr@gmail.com")
    print("  Password: admin123")
    print("  ⚠️  Change this password after your first login!")
db.close()

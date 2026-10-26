
import getpass
from werkzeug.security import generate_password_hash
from app import app, db, User

ADMIN_EMAIL = "rakshitmishra1707@gmail.com"

with app.app_context():
    user = User.query.filter_by(email=ADMIN_EMAIL).first()

    if user:
        user.role = "admin"
        user.is_active = True
        db.session.commit()
        print("Existing account promoted to administrator.")
    else:
        name = input("Administrator display name: ").strip()
        password = getpass.getpass("Create administrator password: ")
        confirm = getpass.getpass("Confirm password: ")

        if not name:
            raise SystemExit("Name cannot be empty.")

        if len(password) < 12:
            raise SystemExit("Use a password of at least 12 characters.")

        if password != confirm:
            raise SystemExit("Passwords do not match.")

        user = User(
            name=name,
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(password),
            role="admin",
            is_active=True,
        )

        db.session.add(user)
        db.session.commit()
        print("Administrator account created successfully.")

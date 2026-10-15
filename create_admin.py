from getpass import getpass
from werkzeug.security import generate_password_hash
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    email = input("Admin email: ").strip().lower()
    if User.query.filter_by(email=email).first():
        print("A user with this email already exists.")
        raise SystemExit
    name = input("Admin name: ").strip()
    password = getpass("Password: ")
    db.session.add(User(name=name, email=email, role="admin",
                        password_hash=generate_password_hash(password)))
    db.session.commit()
    print("Admin created.")
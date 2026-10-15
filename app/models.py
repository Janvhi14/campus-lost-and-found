from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="student")  # student / staff / admin

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(10), nullable=False)       # "lost" or "found"
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    location = db.Column(db.String(100))
    date = db.Column(db.Date)
    image_path = db.Column(db.String(200))
    status = db.Column(db.String(20), default="open")     # open / matched / returned
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"))
    claimant_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    proof = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")  # pending / approved / rejected

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
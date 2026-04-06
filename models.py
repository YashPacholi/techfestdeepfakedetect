from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password      = db.Column(db.String(200), nullable=False)
    is_admin      = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    scans         = db.relationship('Scan', backref='user', lazy=True)
    chats         = db.relationship('Chat', backref='user', lazy=True)

class Scan(db.Model):
    __tablename__ = 'scans'
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename      = db.Column(db.String(200))
    scan_type     = db.Column(db.String(50))
    verdict       = db.Column(db.String(50))
    score         = db.Column(db.Float)
    details       = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

class Chat(db.Model):
    __tablename__ = 'chats'
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message       = db.Column(db.Text, nullable=False)
    response      = db.Column(db.Text, nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    __tablename__ = 'reports'
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scan_id       = db.Column(db.Integer, db.ForeignKey('scans.id'))
    filename      = db.Column(db.String(200))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)


# **3.** Press **Ctrl + S** to save

# ---

# ## ✅ What This File Does
# ```
# models.py = Your DATABASE structure

# User   → stores all registered users
# Scan   → stores every scan result
# Chat   → stores chatbot conversations  
# Report → stores generated PDF reports
# ```

# Think of it like **Excel sheets** — each class is one sheet with columns.

# ---

# ## 🔥 STEP 10 — Create Modules Folder Files

# Now in VS Code — go inside your **modules** folder and create a new file:
# ```
# modules\__init__.py
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os

# ── Create App FIRST ────────────────────────────────
app = Flask(__name__)

# ── Config ─────────────────────────────────────────
app.config['SECRET_KEY']                     = 'deepguard_secret_2024'
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///deepguard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH']             = 50 * 1024 * 1024
app.config['WTF_CSRF_ENABLED']               = False

# ── DB Setup ───────────────────────────────────────
from models import db, User
db.init_app(app)

# ── Extensions ─────────────────────────────────────
csrf      = CSRFProtect(app)
login_mgr = LoginManager(app)
login_mgr.login_view    = 'auth.login'
login_mgr.login_message = 'Please login to access this page.'

@login_mgr.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ── Import Blueprints ──────────────────────────────
from modules.auth       import auth_bp
from modules.detection  import detection_bp
from modules.tools      import tools_bp
from modules.chatbot    import chatbot_bp
from modules.dashboard  import dashboard_bp
from modules.report_gen import reports_bp

# ── Register Blueprints ────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(detection_bp)
app.register_blueprint(tools_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(reports_bp)

# ── Main Routes ────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/emergency')
def emergency():
    return render_template('emergency.html')

@app.route('/learn')
def learn():
    return render_template('awareness.html')

@app.route('/awareness')
def awareness():
    return render_template('awareness.html')

@app.route('/about')
def about():
    return render_template('index.html')

# ── Run App ────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('✅ Database ready!')
    app.run(debug=True, port=5000)
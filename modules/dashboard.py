from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Scan, db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def home():
    scans  = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).limit(10).all()
    total  = Scan.query.filter_by(user_id=current_user.id).count()
    fakes  = Scan.query.filter_by(user_id=current_user.id, verdict='FAKE').count()
    return render_template('dashboard.html', scans=scans, total=total, fakes=fakes)
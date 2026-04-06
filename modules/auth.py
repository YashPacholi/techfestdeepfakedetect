from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm  = request.form.get('confirm_password', '').strip()

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('auth.login'))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.login'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('auth.login'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.login'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return redirect(url_for('auth.login'))

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(
            username=username,
            email=email,
            password=hashed.decode('utf-8')
        )
        db.session.add(user)
        db.session.commit()

        flash('Account created! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Email not found.', 'error')
            return render_template('auth/login.html')

        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            flash('Wrong password.', 'error')
            return render_template('auth/login.html')

        login_user(user)
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('dashboard.home'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))
# ```

# **Ctrl + S**

# ---

# Now run again:
# ```
# C:\Users\LENOVO\AppData\Local\Python\pythoncore-3.14-64\python.exe app.py
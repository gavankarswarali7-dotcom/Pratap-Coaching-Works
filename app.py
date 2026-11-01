from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash
from functools import wraps
import sqlite3
import os
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'pratap-coaching-works-secret-key-change-me'   # session साठी; कोणतीही लांब random string चालेल

GALLERY_DIR = os.path.join(app.static_folder, 'images')
GALLERY_PREVIEW_COUNT = 4   # photos shown before "+N More"


def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        rickshaw_number TEXT,
        service TEXT NOT NULL,
        start_date TEXT,
        end_date TEXT,
        created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

init_db()


def admin_required(view):
    """Admin login नसेल तर login page कडे पाठवतो."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


def _num_key(filename):
    m = re.search(r'\d+', filename)
    return int(m.group()) if m else 0


def gallery_items():
    """Return every gallery photo, grouped roof -> seat -> flap.

    Each item has:
      cat      : 'roof' / 'seat' / 'flap'
      file     : file name inside static/images
      cat_idx  : position inside its category (1, 2, 3, ...)
      preview  : True for the photos shown before the user clicks "+N More"
    """
    groups = {'roof': [], 'seat': [], 'flap': []}
    for f in os.listdir(GALLERY_DIR):
        name, ext = os.path.splitext(f)
        if ext.lower() not in ('.jpg', '.jpeg', '.png', '.webp'):
            continue
        if re.fullmatch(r'flap\d+', name, re.I):
            groups['flap'].append(f)
        elif re.fullmatch(r'seat\d+', name, re.I):
            groups['seat'].append(f)
        elif re.fullmatch(r'(r|rikshaw)\d+', name, re.I):
            groups['roof'].append(f)

    for cat in groups:
        groups[cat].sort(key=_num_key)

    # "All" view preview: 2 roofs + 1 seat + 1 flap
    preview_files = set(groups['roof'][:2] + groups['seat'][:1] + groups['flap'][:1])

    items = []
    for cat in ('roof', 'seat', 'flap'):
        for i, f in enumerate(groups[cat], start=1):
            items.append({
                'cat': cat,
                'file': f,
                'cat_idx': i,
                'preview': f in preview_files,
            })
    return items


@app.route('/')
def home():
    gallery = gallery_items()
    return render_template('index.html', gallery=gallery)

@app.route('/services')
def services():
    return render_template('services.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT id, username, password FROM admin WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()

        if row and check_password_hash(row[2], password):
            session['admin_id'] = row[0]
            session['admin_user'] = row[1]
            return redirect(url_for('admin'))
        error = 'Username किंवा password चुकीचा आहे.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/book', methods=['POST'])
def book():
    name = request.form.get('name')
    phone = request.form.get('phone')
    rickshaw_number = request.form.get('rickshaw_number')
    service = request.form.get('service')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''INSERT INTO bookings
        (name, phone, rickshaw_number, service, start_date, end_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (name, phone, rickshaw_number, service, start_date, end_date, created_at))
    conn.commit()
    conn.close()

    return redirect(url_for('thank_you'))

@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/delete/<int:id>')
@admin_required
def delete_booking(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM bookings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin')
@admin_required
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM bookings ORDER BY created_at DESC')
    bookings = c.fetchall()
    conn.close()
    return render_template('admin.html', bookings=bookings)



if __name__ == '__main__':
    app.run(debug=True)
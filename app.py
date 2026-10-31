from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

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
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('services.html')

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
def delete_booking(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM bookings WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM bookings ORDER BY created_at DESC')
    bookings = c.fetchall()
    conn.close()
    return render_template('admin.html', bookings=bookings)



if __name__ == '__main__':
    app.run(debug=True)
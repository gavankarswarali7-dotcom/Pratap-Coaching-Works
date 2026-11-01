import sqlite3
import getpass
from datetime import datetime
from werkzeug.security import generate_password_hash

# Run this script once to create the first admin.
# How to run: open the project folder and type  ->  python create_admin.py

name = input('Admin name: ').strip()
username = input('Username: ').strip()
password = getpass.getpass('Password (typing will not be shown): ')
password2 = getpass.getpass('Re-enter password: ')

if not username or not password:
    print('Username and password cannot be empty.')
    raise SystemExit(1)
if password != password2:
    print('The two passwords do not match.')
    raise SystemExit(1)

conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TEXT
)''')

try:
    c.execute(
        'INSERT INTO admin (name, username, password, created_at) VALUES (?, ?, ?, ?)',
        (name, username, generate_password_hash(password), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    print(f'Admin "{username}" created successfully.')
except sqlite3.IntegrityError:
    print(f'Username "{username}" already exists. Please use another username.')
finally:
    conn.close()
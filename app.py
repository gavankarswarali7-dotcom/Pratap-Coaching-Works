import sqlite3
import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
DB_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Customers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            vehicle_no TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Services catalog
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            description TEXT,
            default_price REAL NOT NULL
        )
    ''')
    
    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            vehicle_no TEXT,
            subtotal REAL NOT NULL,
            discount REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            paid_amount REAL NOT NULL,
            pending_balance REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Order items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            rate REAL NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
        )
    ''')
    
    # Payments log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_mode TEXT NOT NULL,
            notes TEXT,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
        )
    ''')
    
    # Wipe and re-seed services with clean catalog (4 categories)
    cursor.execute('DELETE FROM services')
    all_services = [
        # --- SEAT COVERS ---
        ('Seat Covers (Front & Back)', 'Seat Covers', 'Cushioned rexine/leatherette front and back seat upholstery.', 2800.0),
        ('Single Seat Cover', 'Seat Covers', 'Replacement cover for one seat — driver or passenger.', 900.0),
        ('Deluxe Velvet Seat Covers', 'Seat Covers', 'Premium soft velvet fabric covers with embroidered design.', 3200.0),
        ('Seat Cover Repair & Stitching', 'Seat Covers', 'Patch repair or re-stitching of existing seat cover.', 500.0),

        # --- ROOFTOP COVERS ---
        ('Rooftop Waterproof Hood / Canopy', 'Rooftop Cover', 'Heavy-duty waterproof PVC rooftop cover with steel-loop fittings.', 3500.0),
        ('Hood Repair & Stitching', 'Rooftop Cover', 'Patch repair, re-stitching or waterproofing of existing hood.', 800.0),
        ('Side Curtains / Rain Covers', 'Rooftop Cover', 'Transparent PVC side curtains for rain and wind protection.', 1100.0),
        ('Deluxe Rooftop Cover (Heavy Fabric)', 'Rooftop Cover', 'Thick canvas rooftop cover with premium stitching and border.', 4500.0),

        # --- TYRE FLAPS ---
        ('Mud Flaps (Set of 4)', 'Tyre Flaps', 'Durable rubber mud flaps — plain or with name/branding print.', 650.0),
        ('Heavy Duty Mud Flaps (Set of 4)', 'Tyre Flaps', 'Thick molded rubber mud flaps for heavy-duty protection.', 950.0),
        ('Rear Splash Guard', 'Tyre Flaps', 'Rear-only heavy rubber splash guard fitting.', 350.0),
    ]
    cursor.executemany(
        'INSERT INTO services (name, category, description, default_price) VALUES (?, ?, ?, ?)',
        all_services
    )

    conn.commit()
    conn.close()

# Initialize DB
init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/management')
def management():
    return render_template('management.html')

@app.route('/bill/<int:order_id>')
def view_bill(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        conn.close()
        return "Invoice not found", 404
        
    items = conn.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,)).fetchall()
    payments = conn.execute('SELECT * FROM payments WHERE order_id = ? ORDER BY payment_date DESC', (order_id,)).fetchall()
    conn.close()
    
    return render_template('bill_invoice.html', order=order, items=items, payments=payments)

# --- REST APIs ---

@app.route('/api/initial_data')
def get_initial_data():
    conn = get_db_connection()
    services_list = [dict(row) for row in conn.execute('SELECT * FROM services ORDER BY name ASC').fetchall()]
    orders_list = [dict(row) for row in conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()]
    
    # Pending balances summary
    pending_summary = [dict(row) for row in conn.execute('''
        SELECT id, invoice_no, customer_name, customer_phone, vehicle_no, total_amount, paid_amount, pending_balance, created_at, status
        FROM orders 
        WHERE pending_balance > 0 
        ORDER BY id DESC
    ''').fetchall()]
    
    conn.close()
    return jsonify({
        'services': services_list,
        'orders': orders_list,
        'pending_summary': pending_summary
    })

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    if not data or 'customer_name' not in data or 'items' not in data or len(data['items']) == 0:
        return jsonify({'error': 'Customer name and at least one service item are required.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Generate Invoice Number PCW-YYYY-XXX
        year = datetime.datetime.now().strftime('%Y')
        cursor.execute('SELECT COUNT(*) FROM orders')
        count = cursor.fetchone()[0] + 1
        invoice_no = f"PCW-{year}-{count:04d}"
        
        customer_name = data.get('customer_name', '').strip()
        customer_phone = data.get('customer_phone', '').strip()
        vehicle_no = data.get('vehicle_no', '').strip().upper()
        
        # Save Customer Record
        cursor.execute('SELECT id FROM customers WHERE phone = ?', (customer_phone,))
        cust = cursor.fetchone()
        if not cust and customer_phone:
            cursor.execute('INSERT INTO customers (name, phone, vehicle_no) VALUES (?, ?, ?)', 
                           (customer_name, customer_phone, vehicle_no))
            
        items = data['items']
        subtotal = sum(float(item['rate']) * int(item['quantity']) for item in items)
        discount = float(data.get('discount', 0))
        tax_amount = float(data.get('tax_amount', 0))
        total_amount = max(0, subtotal - discount + tax_amount)
        
        paid_amount = float(data.get('paid_amount', 0))
        pending_balance = max(0, total_amount - paid_amount)
        
        status = 'Completed' if pending_balance == 0 else 'Pending Payment'
        
        # Insert Order
        cursor.execute('''
            INSERT INTO orders (invoice_no, customer_name, customer_phone, vehicle_no, subtotal, discount, tax_amount, total_amount, paid_amount, pending_balance, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (invoice_no, customer_name, customer_phone, vehicle_no, subtotal, discount, tax_amount, total_amount, paid_amount, pending_balance, status))
        
        order_id = cursor.lastrowid
        
        # Insert Line Items
        for item in items:
            s_name = item.get('service_name', 'Custom Service')
            qty = int(item.get('quantity', 1))
            rate = float(item.get('rate', 0))
            amt = qty * rate
            
            cursor.execute('''
                INSERT INTO order_items (order_id, service_name, quantity, rate, amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, s_name, qty, rate, amt))

        # Log Payment
        if paid_amount > 0:
            payment_mode = data.get('payment_mode', 'Cash')
            cursor.execute('''
                INSERT INTO payments (order_id, amount, payment_mode, notes)
                VALUES (?, ?, ?, ?)
            ''', (order_id, paid_amount, payment_mode, 'Initial payment upon order creation'))

        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'invoice_no': invoice_no,
            'total_amount': total_amount,
            'pending_balance': pending_balance
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments', methods=['POST'])
def record_payment():
    data = request.json
    order_id = data.get('order_id')
    amount = float(data.get('amount', 0))
    payment_mode = data.get('payment_mode', 'Cash')
    notes = data.get('notes', 'Balance payment collected')
    
    if not order_id or amount <= 0:
        return jsonify({'error': 'Valid order ID and positive payment amount required.'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT total_amount, paid_amount, pending_balance FROM orders WHERE id = ?', (order_id,))
    order = cursor.fetchone()
    if not order:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404
        
    new_paid = order['paid_amount'] + amount
    new_balance = max(0, order['total_amount'] - new_paid)
    new_status = 'Completed' if new_balance == 0 else 'Pending Payment'
    
    cursor.execute('''
        UPDATE orders SET paid_amount = ?, pending_balance = ?, status = ? WHERE id = ?
    ''', (new_paid, new_balance, new_status, order_id))
    
    cursor.execute('''
        INSERT INTO payments (order_id, amount, payment_mode, notes)
        VALUES (?, ?, ?, ?)
    ''', (order_id, amount, payment_mode, notes))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'paid_amount': new_paid,
        'pending_balance': new_balance,
        'status': new_status
    })

@app.route('/api/services', methods=['POST'])
def manage_services():
    data = request.json
    s_id = data.get('id')
    name = data.get('name', '').strip()
    category = data.get('category', 'General').strip()
    description = data.get('description', '').strip()
    default_price = float(data.get('default_price', 0))
    
    if not name:
        return jsonify({'error': 'Service name is required'}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if s_id:
        cursor.execute('''
            UPDATE services SET name=?, category=?, description=?, default_price=? WHERE id=?
        ''', (name, category, description, default_price, s_id))
    else:
        cursor.execute('''
            INSERT INTO services (name, category, description, default_price) VALUES (?, ?, ?, ?)
        ''', (name, category, description, default_price))
        
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
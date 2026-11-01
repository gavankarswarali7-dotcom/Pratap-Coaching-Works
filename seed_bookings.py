import sqlite3

# 35 sample bookings (at least 7 per service) spread over about 3 months (Aug 2026 to Oct 2026).
# Columns: name, phone, rickshaw_number, service, start_date, end_date, created_at
SAMPLE_ROWS = [
    ("Ramesh Patil",       "9423011101", "MH 09 AB 1201", "roof_custom", "2026-08-03", "2026-08-05", "2026-08-01 10:15:00"),
    ("Sanjay Jadhav",      "9822033302", "MH 12 CD 2345", "seat_custom", "2026-08-04", "2026-08-05", "2026-08-02 11:20:00"),
    ("Anil Kadam",         "9764544403", "MH 10 EF 3456", "tyre_flaps",  "2026-08-06", "2026-08-08", "2026-08-05 09:05:00"),
    ("Vijay Mane",         "9850112204", "MH 10 GH 4567", "roof_seat",   "2026-08-10", "2026-08-13", "2026-08-08 14:40:00"),
    ("Ganesh Shinde",      "9730876505", "MH 10 JK 5678", "complete",    "2026-08-14", "2026-08-20", "2026-08-12 16:30:00"),
    ("Suresh Pawar",       "9405522106", "MH 10 LM 6789", "roof_custom", "2026-08-18", "2026-08-20", "2026-08-16 10:00:00"),
    ("Mahesh Gaikwad",     "9921304407", "MH 12 NP 7890", "seat_custom", "2026-08-23", "2026-08-24", "2026-08-21 12:25:00"),
    ("Dattatray Salunkhe", "9028745608", "MH 09 QR 8901", "tyre_flaps",  "2026-08-28", "2026-08-29", "2026-08-26 09:50:00"),
    ("Prakash Bhosale",    "9637018709", "MH 10 ST 9012", "roof_seat",   "2026-09-02", "2026-09-05", "2026-08-31 15:10:00"),
    ("Tanaji Desai",       "9766429810", "MH 11 UV 0123", "complete",    "2026-09-08", "2026-09-14", "2026-09-06 11:45:00"),
    ("Shivaji Kamble",     "9881163211", "MH 09 BC 2233", "roof_custom", "2026-09-14", "2026-09-15", "2026-09-12 10:30:00"),
    ("Balasaheb Ghadge",   "9579210012", "KA 22 DE 3344", "seat_custom", "2026-09-19", "2026-09-21", "2026-09-17 13:00:00"),
    ("Raju Chavan",        "9372845613", "MH 13 FG 4455", "tyre_flaps",  "2026-09-24", "2026-09-25", "2026-09-22 09:20:00"),
    ("Nitin Hingmire",     "9011376614", "MH 12 HI 5566", "roof_seat",   "2026-09-29", "2026-10-02", "2026-09-27 17:00:00"),
    ("Kiran Sawant",       "9822507715", "MH 14 JL 6677", "complete",    "2026-10-05", "2026-10-11", "2026-10-03 10:35:00"),
    ("Yogesh More",        "9623419816", "KA 25 KM 7788", "roof_custom", "2026-10-12", "2026-10-14", "2026-10-10 12:50:00"),
    ("Rahul Naik",         "9765008817", "MH 10 NO 8899", "seat_custom", "2026-10-18", "2026-10-19", "2026-10-16 11:10:00"),
    ("Sachin Kulkarni",    "9404667718", "MH 15 PQ 9900", "tyre_flaps",  "2026-10-23", "2026-10-24", "2026-10-21 16:20:00"),
    ("Amol Thorat",        "9850329019", "MH 15 RS 1020", "roof_seat",   "2026-10-27", "2026-10-30", "2026-10-25 09:40:00"),
    ("Dhanaji Mohite",     "9689154320", "MH 13 TU 2030", "complete",    "2026-10-30", "2026-11-05", "2026-10-28 14:05:00"),
    ("Harshad Pol",        "9766012121", "MH 14 VA 1111", "roof_custom", "2026-08-25", "2026-08-27", "2026-08-22 10:00:00"),
    ("Dilip Lad",          "9421733122", "MH 09 VB 2222", "roof_custom", "2026-09-10", "2026-09-12", "2026-09-08 11:30:00"),
    ("Kedar Joshi",        "9850244123", "KA 22 VC 3333", "roof_custom", "2026-10-20", "2026-10-22", "2026-10-18 15:45:00"),
    ("Ajay Mhetre",        "9822355124", "MH 12 VD 4444", "seat_custom", "2026-08-30", "2026-08-31", "2026-08-27 09:15:00"),
    ("Pravin Sutar",       "9373466125", "MH 11 VE 5555", "seat_custom", "2026-09-08", "2026-09-09", "2026-09-05 12:20:00"),
    ("Sunil Kore",         "9011577126", "MH 09 VF 6666", "seat_custom", "2026-10-14", "2026-10-16", "2026-10-12 16:10:00"),
    ("Ravi Bandgar",       "9764688127", "MH 15 VG 7777", "tyre_flaps",  "2026-08-19", "2026-08-20", "2026-08-17 10:50:00"),
    ("Mangesh Patil",      "9552799128", "MH 10 VH 8888", "tyre_flaps",  "2026-09-16", "2026-09-17", "2026-09-14 13:35:00"),
    ("Umesh Jagtap",       "9823810129", "MH 10 VJ 9999", "tyre_flaps",  "2026-10-07", "2026-10-08", "2026-10-05 09:00:00"),
    ("Atul Deshmukh",      "9637921130", "MH 13 VK 1212", "roof_seat",   "2026-08-13", "2026-08-16", "2026-08-11 14:00:00"),
    ("Santosh Kale",       "9284032131", "MH 14 VL 2323", "roof_seat",   "2026-09-04", "2026-09-07", "2026-09-02 11:10:00"),
    ("Hemant Varpe",       "9011245132", "MH 12 VM 3434", "roof_seat",   "2026-10-16", "2026-10-18", "2026-10-14 10:25:00"),
    ("Lalit Gawde",        "9860656133", "MH 10 VN 4545", "complete",    "2026-08-07", "2026-08-14", "2026-08-04 15:00:00"),
    ("Vishal Rane",        "9657317134", "KA 25 VP 5656", "complete",    "2026-09-21", "2026-09-27", "2026-09-19 11:40:00"),
    ("Pankaj Gite",        "9423908135", "MH 10 VQ 6767", "complete",    "2026-10-22", "2026-10-29", "2026-10-20 09:55:00"),
]

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Make sure the table exists (same schema as app.py)
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

# Remove earlier sample rows (same phone numbers) so running this again
# replaces them instead of adding duplicates.
phones = [row[1] for row in SAMPLE_ROWS]
placeholders = ','.join('?' * len(phones))
c.execute(f'DELETE FROM bookings WHERE phone IN ({placeholders})', phones)
removed = c.rowcount

c.executemany(
    '''INSERT INTO bookings
       (name, phone, rickshaw_number, service, start_date, end_date, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)''',
    SAMPLE_ROWS
)

conn.commit()
conn.close()
print(f"Removed {removed} old sample rows. Added {len(SAMPLE_ROWS)} new records.")
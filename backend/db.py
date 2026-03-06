import sqlite3
import os
from passlib.context import CryptContext

DB_FILE = 'safeworks.db'

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def get_password_hash(password):
    return pwd_context.hash(password)

def init_db():
    if os.path.exists(DB_FILE):
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create users
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password_hash TEXT,
        role TEXT,
        name TEXT
    )
    ''')

    # Create requirements
    cursor.execute('''
    CREATE TABLE requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hc_id INTEGER,
        name TEXT,
        description TEXT,
        workers_required INTEGER,
        start_date TEXT,
        ai_validated_description TEXT,
        FOREIGN KEY(hc_id) REFERENCES users(id)
    )
    ''')

    # Create workers
    cursor.execute('''
    CREATE TABLE workers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contractor_id INTEGER,
        name TEXT,
        certifications TEXT,
        years_experience INTEGER,
        FOREIGN KEY(contractor_id) REFERENCES users(id)
    )
    ''')

    # Create submissions
    cursor.execute('''
    CREATE TABLE submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        requirement_id INTEGER,
        contractor_id INTEGER,
        worker_ids TEXT,
        suggested_rate REAL,
        readiness_date TEXT,
        FOREIGN KEY(requirement_id) REFERENCES requirements(id),
        FOREIGN KEY(contractor_id) REFERENCES users(id)
    )
    ''')

    # Create requirement assignments
    cursor.execute('''
    CREATE TABLE requirement_assignments (
        requirement_id INTEGER,
        contractor_id INTEGER,
        PRIMARY KEY(requirement_id, contractor_id),
        FOREIGN KEY(requirement_id) REFERENCES requirements(id),
        FOREIGN KEY(contractor_id) REFERENCES users(id)
    )
    ''')

    # Seed Users
    default_password = get_password_hash("password123")
    
    users_data = [
        # Hiring Clients
        ('hc1@test.com', default_password, 'hc', 'HC Alpha'),
        ('hc2@test.com', default_password, 'hc', 'HC Beta'),
        ('hc3@test.com', default_password, 'hc', 'HC Gamma'),
        
        # Safeworks User
        ('safeworks@test.com', default_password, 'safeworks', 'Safeworks Administrator'),
        
        # Contractors
        ('c1@test.com', default_password, 'contractor', 'Builder One'),
        ('c2@test.com', default_password, 'contractor', 'Builder Two'),
        ('c3@test.com', default_password, 'contractor', 'Builder Three')
    ]

    cursor.executemany('''
    INSERT INTO users (email, password_hash, role, name)
    VALUES (?, ?, ?, ?)
    ''', users_data)

    # Seed Workers for Contractors
    workers_data = [
        (5, 'Alice Smith', 'OSHA 30, CPR', 5),
        (5, 'Bob Jones', 'Heavy Machinery', 8),
        (6, 'Charlie Brown', 'Welding, First Aid', 3),
        (7, 'David White', 'Electrician Master', 12),
        (7, 'Eve Black', 'Crane Operator', 6)
    ]
    
    cursor.executemany('''
    INSERT INTO workers (contractor_id, name, certifications, years_experience)
    VALUES (?, ?, ?, ?)
    ''', workers_data)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized recursively.")

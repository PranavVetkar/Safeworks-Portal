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

def migrate_db():
    """Safely apply schema migrations on existing DB (idempotent)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Add new columns to submissions if missing
    existing_cols = [row[1] for row in cursor.execute("PRAGMA table_info(submissions)").fetchall()]
    new_cols = [
        ('workers_committed', 'INTEGER DEFAULT 0'),
        ('workers_ready', 'INTEGER DEFAULT 0'),
        ('workers_to_onboard', 'INTEGER DEFAULT 0'),
    ]
    for col_name, col_def in new_cols:
        if col_name not in existing_cols:
            cursor.execute(f'ALTER TABLE submissions ADD COLUMN {col_name} {col_def}')

    # Add area_of_experience to workers if missing
    worker_cols = [row[1] for row in cursor.execute("PRAGMA table_info(workers)").fetchall()]
    if 'area_of_experience' not in worker_cols:
        cursor.execute("ALTER TABLE workers ADD COLUMN area_of_experience TEXT DEFAULT 'General Construction'")

    # Create worker_courses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS worker_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id INTEGER,
        course_name TEXT,
        FOREIGN KEY(worker_id) REFERENCES workers(id)
    )
    ''')

    # Create shortlisted_contractors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shortlisted_contractors (
        requirement_id INTEGER,
        contractor_id INTEGER,
        PRIMARY KEY(requirement_id, contractor_id),
        FOREIGN KEY(requirement_id) REFERENCES requirements(id),
        FOREIGN KEY(contractor_id) REFERENCES users(id)
    )
    ''')

    # Seed missing workers so each contractor has 10
    # WORKER_SEED is defined below — Python resolves it at call-time, not definition-time
    for contractor_id, name, certs, years, area in WORKER_SEED:
        cursor.execute(
            "SELECT COUNT(*) FROM workers WHERE contractor_id = ? AND name = ?",
            (contractor_id, name)
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO workers (contractor_id, name, certifications, years_experience, area_of_experience) VALUES (?, ?, ?, ?, ?)",
                (contractor_id, name, certs, years, area)
            )

    conn.commit()
    conn.close()

# Full worker seed list: 10 per contractor (contractor_ids: 5, 6, 7)
WORKER_SEED = [
    # Contractor 5 - Builder One
    (5, 'Alice Smith',      'OSHA 30, CPR',                       5,  'Structural Steel'),
    (5, 'Bob Jones',        'Heavy Machinery, Rigging',           8,  'Heavy Equipment'),
    (5, 'Carlos Vega',      'OSHA 10, Fall Protection',          3,  'General Construction'),
    (5, 'Diana Patel',      'First Aid, Scaffolding',             6,  'Scaffolding'),
    (5, 'Ethan Brooks',     'Confined Space, HAZMAT',            10,  'Industrial Safety'),
    (5, 'Fatima Noor',      'CPR, Welding Level 2',               4,  'Welding'),
    (5, 'George Liu',       'Electrician Journeyman',             7,  'Electrical'),
    (5, 'Hannah Roy',       'Crane Operator, OSHA 30',            9,  'Crane Operations'),
    (5, 'Ivan Petrov',      'Concrete Finishing, OSHA 10',        2,  'Concrete Works'),
    (5, 'Julia Torres',     'Plumbing, Fall Protection',          5,  'Plumbing'),
    # Contractor 6 - BuildWell Inc.
    (6, 'Charlie Brown',    'Welding, First Aid',                 3,  'Welding'),
    (6, 'Karla Mendez',     'OSHA 30, Rigging',                  6,  'Rigging & Lifting'),
    (6, 'Liam O Connor',   'Heavy Equipment, CPR',               8,  'Heavy Equipment'),
    (6, 'Maya Singh',       'Scaffolding, OSHA 10',               4,  'Scaffolding'),
    (6, 'Nathan Cole',      'Electrician Master, OSHA 30',        11, 'Electrical'),
    (6, 'Olivia Hart',      'HAZMAT, Confined Space',             5,  'Hazardous Materials'),
    (6, 'Pedro Alves',      'Concrete, Fall Protection',          7,  'Concrete Works'),
    (6, 'Quinn Zhang',      'Piping, OSHA 10',                    3,  'Piping & Mechanical'),
    (6, 'Rachel Kim',       'Welding Level 3, First Aid',         9,  'Welding'),
    (6, 'Samuel Wright',    'Crane Operator, Rigging',            12, 'Crane Operations'),
    # Contractor 7 - City Scaffolders
    (7, 'David White',      'Electrician Master, OSHA 30',        12, 'Electrical'),
    (7, 'Eve Black',        'Crane Operator, CPR',                6,  'Crane Operations'),
    (7, 'Tom Harris',       'Scaffolding Adv, OSHA 30',           8,  'Scaffolding'),
    (7, 'Uma Patel',        'Fall Protection, First Aid',         4,  'General Construction'),
    (7, 'Victor Novak',     'Heavy Machinery, OSHA 10',           5,  'Heavy Equipment'),
    (7, 'Wendy Adams',      'Welding, HAZMAT',                    7,  'Welding'),
    (7, 'Xavier Diaz',      'Electrical, Confined Space',         9,  'Electrical'),
    (7, 'Yara Hassan',      'Plumbing, OSHA 30',                  3,  'Plumbing'),
    (7, 'Zach Martin',      'Rigging, Crane Level 1',             6,  'Rigging & Lifting'),
    (7, 'Amelia Johansson', 'OSHA 30, Metal Framing',             11, 'Structural Steel'),
]

def init_db():
    if os.path.exists(DB_FILE):
        migrate_db()  # Always apply migrations to existing DB
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
        readiness_date TEXT,
        workers_committed INTEGER DEFAULT 0,
        workers_ready INTEGER DEFAULT 0,
        workers_to_onboard INTEGER DEFAULT 0,
        FOREIGN KEY(requirement_id) REFERENCES requirements(id),
        FOREIGN KEY(contractor_id) REFERENCES users(id)
    )
    ''')

    # Create worker_courses table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS worker_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id INTEGER,
        course_name TEXT,
        FOREIGN KEY(worker_id) REFERENCES workers(id)
    )
    ''')

    # Create shortlisted_contractors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shortlisted_contractors (
        requirement_id INTEGER,
        contractor_id INTEGER,
        PRIMARY KEY(requirement_id, contractor_id),
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

    # Seed Workers for Contractors — 10 per contractor
    cursor.executemany('''
    INSERT INTO workers (contractor_id, name, certifications, years_experience, area_of_experience)
    VALUES (?, ?, ?, ?, ?)
    ''', WORKER_SEED)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized recursively.")

import sqlite3
from flask import g

DATABASE = "database.db"

def seed_admin_data(db):
    cursor = db.cursor()

    # Example admin accounts
    admins = [
        ("ADMIN001", "adminpass123"),
        ("ADMIN002", "securepass456")
    ]

    for id_number, password in admins:
        # Insert only if not exists
        cursor.execute(
            "INSERT OR IGNORE INTO admins (id_number, password) VALUES (?, ?)",
            (id_number, password)
        )
    
    db.commit()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=30
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode = WAL")
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def setup_database(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL CHECK(length(first_name) <= 30),
            middle_name TEXT CHECK(length(middle_name) <= 30),
            last_name TEXT NOT NULL CHECK(length(last_name) <= 30),
            course_level INTEGER NOT NULL CHECK(course_level BETWEEN 1 AND 4),
            course TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            address TEXT NOT NULL,
            sessions_remaining INTEGER NOT NULL DEFAULT 30 CHECK(sessions_remaining BETWEEN 0 AND 30),
            total_session_used INTEGER NOT NULL DEFAULT 0 CHECK(total_session_used >= 0)
            )

        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
            )
                       
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions_history(
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            login_time TEXT,
            logout_time TEXT,
            session_date TEXT NOT NULL,
            pc_number TEXT,
            lab_room TEXT,       
            FOREIGN KEY(student_id) REFERENCES students(id)
        )



        """)
        db.commit()
        seed_admin_data(db)
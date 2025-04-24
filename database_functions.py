import sqlite3

# -------------------- Database Functions --------------------
def create_database():
    """Creates the SQLite database and required tables."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    
    # Users table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')
    
    # User profile table linked to users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY,
            dob DATE,
            gender TEXT,
            family_size INTEGER,
            num_pets INTEGER,
            city TEXT,
            education INTEGER,
            remote_percentage FLOAT,
            job TEXT,
            name TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Burnout history table linked to users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS burnout_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TIMESTAMP,
            risk_percentage FLOAT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # To-do list table linked to users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todo_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task TEXT,
            completed BOOLEAN,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Table to track the last scheduled task
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_tasks (
            user_id INTEGER PRIMARY KEY,
            last_scheduled TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Add a table to store Fitbit tokens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fitbit_tokens (
            email TEXT PRIMARY KEY,
            access_token TEXT,
            refresh_token TEXT,
            token_expiry TIMESTAMP
        )
    ''')

    # Add a table to track daily stress survey submissions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stress_submissions (
            user_id INTEGER PRIMARY KEY,
            last_submission TIMESTAMP,
            mood TEXT,
            stress_level INTEGER,
            work_hours FLOAT,
            weekend_overtime FLOAT,
            exercise_hours FLOAT,
            sleep_hours FLOAT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def update_database_schema():
    """Updates the database schema to include missing columns."""
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    # Add missing columns to the daily_stress_submissions table
    try:
        cursor.execute("ALTER TABLE daily_stress_submissions ADD COLUMN mood TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    try:
        cursor.execute("ALTER TABLE daily_stress_submissions ADD COLUMN stress_level INTEGER")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE daily_stress_submissions ADD COLUMN work_hours FLOAT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE daily_stress_submissions ADD COLUMN weekend_overtime FLOAT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE daily_stress_submissions ADD COLUMN exercise_hours FLOAT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE daily_stress_submissions ADD COLUMN sleep_hours FLOAT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()
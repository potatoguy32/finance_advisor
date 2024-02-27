import sqlite3


def create_db():
    # Create (connect) database
    conn = sqlite3.connect("finance_advisor_db.db")
    cur = conn.cursor()

    # Create users and passwords tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        etf_symbol TEXT NOT NULL,
        company_symbol TEXT NOT NULL,
        
        
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        master_password TEXT NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS Passwords(
        pass_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        site TEXT,
        url TEXT,
        email TEXT,
        site_username TEXT,
        password TEXT NOT NULL
    );
    """)

    # Commit changes
    conn.commit()
    # Close database
    conn.close()
    return
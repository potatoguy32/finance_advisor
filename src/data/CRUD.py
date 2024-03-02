def create_db(connection):
    # Create (connect) database
    cur = connection.cursor()

    # Create users and passwords tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS news (
        etf_symbol TEXT NOT NULL,
        company_symbol TEXT NOT NULL,
        date TIMESTAMP NOT NULL,
        uuid TEXT,
        title TEXT,
        description TEXT,
        match_score FLOAT,
        sentiment_score FLOAT,
        PRIMARY KEY(etf_symbol, company_symbol, date, uuid)
    );
    """)
    connection.commit()
    return

def load_news_data(connection, data):
    create_db(connection=connection)
    cur = connection.cursor()
    cur.executemany("""INSERT INTO news VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", data)
    connection.commit()
    return

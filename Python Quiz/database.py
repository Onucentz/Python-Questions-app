import sqlite3

DB_NAME = "quiz_system.db"


def init_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            firstname TEXT,
            surname TEXT,
            class_name TEXT,

            score INTEGER,
            percentage REAL,

            timestamp TEXT

        )
    """)

    conn.commit()
    conn.close()


def save_result(firstname, surname, class_name, score, percentage, timestamp):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO results (
            firstname,
            surname,
            class_name,
            score,
            percentage,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        firstname,
        surname,
        class_name,
        score,
        percentage,
        timestamp
    ))

    conn.commit()
    conn.close()
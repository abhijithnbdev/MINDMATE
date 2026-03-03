import psycopg2
import psycopg2.extras
import os

# Database Connection Configuration
PG_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "dbname": "mindmate",
    "user": "mindmate_user",
    "password": "mindmate123"
}


def get_db():
    """Establishes a connection to the PostgreSQL database."""
    conn = psycopg2.connect(**PG_CONFIG)
    # This allows row['column_name'] access like SQLite's Row factory
    return conn

def get_cursor(conn):
    """Returns a dictionary-like cursor."""
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
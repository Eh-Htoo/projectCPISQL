import os
import mysql.connector

from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Open a new MySQL connection using the values in .env.

    The caller is responsible for closing it (conn.close()).
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
    )
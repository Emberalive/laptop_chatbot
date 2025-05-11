import os

from psycopg2 import pool
import sys
from dotenv import load_dotenv
from loguru import logger

logger.add(sys.stdout, format="{time} {level} {message}")
logger.add("../logs/database.log", rotation="2 MB", retention="20 days", compression="zip")
logger = logger.bind(user="database")

connection_pool = None


def init_db_pool():
    global connection_pool
    load_dotenv()
    try:
        logger.info("Creating PostgreSQL connection pool...")
        connection_pool = pool.SimpleConnectionPool(
            minconn = 1,
            maxconn = 400,
            database = os.getenv("DATABASE_NAME"),
            user= os.getenv("USER"),
            host = os.getenv("DB_HOST"),
            password = os.getenv("PASSWORD"),
            port = 5432
        )
        logger.info("Connection pool created successfully")
    except Exception as e:
        logger.error(f"Failed to create the connection pool {e}")

def get_db_connection():
    try:
        logger.info(f"grabbing a connection from the pool")
        conn = connection_pool.getconn()
        if conn:
            cur = conn.cursor()
            logger.info("Connection successful")
            return conn, cur
        else:
            logger.error("No connection available in the pool")
            return None, None
    except Exception as e:
        logger.error(f"Failed to get connection {e}")
        return None, None

def release_db_connection(conn, cur):
    try :
        if cur:
            cur.close()
        if conn:
            connection_pool.putconn(conn)  # Return connection to pool
        logger.info("Connection has been returned to the pool")
    except Exception as e:
        logger.error(f"Error releasing connection: {e}")

def db_access():
    try:
        print("Attempting connection to the database\n")
        # put this is your name and password until we're at point where we can insert
        conn = psycopg2.connect(database = "laptopchatbot",
            user = "samuel",
            host = "86.19.219.159",
            password = "QwErTy1243!",
            port = 5432)

        # Creating a cursor with name cur, allows queries to the db
        cur = conn.cursor()
        print('Connected to the PostgreSQL database\n')
        return conn, cur
    except Exception as e:
        print("connection was not made. Error: {e}")


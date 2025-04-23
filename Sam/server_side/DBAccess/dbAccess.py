import psycopg2
from psycopg2 import pool

connection_pool = None


def init_db_pool():
    global connection_pool
    try:
        print("Creating PostgreSQL connection pool...")
        connection_pool = pool.SimpleConnectionPool(
            minconn = 1,
            maxconn = 400,
            database = "laptopchatbot_new",
            user= "samuel",
            host = "86.19.219.159",
            password = "QwErTy1243!",
            port = 5432
        )
        print("Connection pool created successfully")
    except Exception as e:
        print(f"Failed to create the connection pool {e}")

def get_db_connection():
    try:
        conn = connection_pool.getconn()
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(f"Failed to get connection {e}")

def release_db_connection(conn, cur):
    try :
        if cur:
            cur.close()
        if conn:
            connection_pool.putconn(conn)  # Return connection to pool
        print("Connection has been returned to the pool")
    except Exception as e:
        print(f"Error releasing connection: {e}")

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

init_db_pool()
conn, cur = get_db_connection()
release_db_connection(conn, cur)
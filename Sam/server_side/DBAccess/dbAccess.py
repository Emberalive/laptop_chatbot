# you need to install pip
# and then using pip install psycopg2-binary

import psycopg2

def db_access():
    try:
        print("Attempting connection to the database\n")
        # put this is your name and password until we're at point where we can insert
        conn = psycopg2.connect(database = "laptopchatbot",
            user = "samuel",
            host = "192.168.0.144",
            # host = "10.8.18.92",
            password = "QwErTy1243!",
            port = 5432)

        # Creating a cursor with name cur, allows queries to the db
        cur = conn.cursor()
        print('Connected to the PostgreSQL database\n')
        return conn, cur
    except Exception as e:
        print("connection was not made. Error: {e}")

db_access()
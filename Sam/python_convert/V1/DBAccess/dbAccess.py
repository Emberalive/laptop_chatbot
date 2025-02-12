# you need to install pip
# and then using pip install psycopg2-binary

import psycopg2

def bd_access():
    try:
        conn = psycopg2.connect(database = "laptopchatbot",
            user = "samuel",
            host = "192.168.0.144",
            password = "QwErTy1243!",
            port = 5432)

        # Creating a cursor with name cur, allows queries to the db
        cur = conn.cursor()
        print('Connected to the PostgreSQL database')
        return conn, cur
    except conn:
        print("connection was not made")

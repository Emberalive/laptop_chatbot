# you need to install pip
# and then using pip install psycopg2-binary

import psycopg2

def bd_access():
    try:
        # put this is your name and password until we're at point where we can insert
        conn = psycopg2.connect(database = "laptopchatbot",
            user = "your_username",
            host = "192.168.0.144",
            password = "your_pass",
            port = 5432)

        # Creating a cursor with name cur, allows queries to the db
        cur = conn.cursor()
        print('Connected to the PostgreSQL database')
        return conn, cur
    except conn:
        print("connection was not made")

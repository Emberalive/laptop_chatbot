from DBAccess.dbAccess import db_access

# im selecting a view that generates a fake password hash, but the passwords are actually stored in the database

# importing the connection and the cursor from the dbaccess function
conn, cur = db_access()

# checking if the objects exist
if conn and cur:
    try:
        # running a query
        cur.execute('SELECT * FROM user_info')
        # printing all the results from the query
        print("Query Results: \n")
        for query in cur:
            print(str(query))
    except Exception as e:
        print(f"Query execution failed: {e}")
    finally:
        # closing the cursor and the connection if the connection failed
        cur.close()
        conn.close()
else:
    print("Failed to connect to the database")
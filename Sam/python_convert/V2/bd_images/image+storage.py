from V1.DBAccess.dbAccess import bd_access
from V2.bd_images.image_insertion import image_data

# im selecting a view that generates a fake password hash, but the passwords are actually stored in the database

# importing the connection and the cursor from the dbaccess function
conn, cur = bd_access()

# checking if the objects exist
if conn and cur:
    try:
        # running a query
        cur.execute('SELECT * FROM images')

        image_data = cur.fetchone() # fetches the first row

        if image_data and image_data[0]:
            save_path = './images/saved_image.jpg'

            with open (save_path, "wb") as file:
                file.write(image_data[0])
            print("image has been saved to {./bd_images/images/saved_image.jpg}")
        else:
            print(f"No image was found")

    except Exception as e:
        print(f"Query execution failed: {e}")
    finally:
        # closing the cursor and the connection if the connection failed
        cur.close()
        conn.close()
else:
    print("Failed to connect to the database")

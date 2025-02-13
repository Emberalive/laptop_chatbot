from V1.DBAccess.dbAccess import bd_access

conn, cur = bd_access()

def image_to_bytea():
    with open('images/imageStock.jpg', 'rb') as file: # rb means read binary values the with clause makes sure the file is closed after read
        return file.read()

if conn and cur:
    image_path = 'images/imageStock.jpg'

    image_data = image_to_bytea()

    try:
        query2 = """
                INSERT INTO laptops (model, brand, screensize, price, weight, batterylife, memory)
                VALUES ('model1', 'brand1', 15.2, 300, '22kg', '2hours', 'ddr4');
        """
        cur.execute(query2)

        query = """
                INSERT INTO images (image, laptop)
                 VALUES (%s, %s);
                 """
        cur.execute(query, (image_data, 'model1'))
        conn.commit()
        print("image inserted successfully")
    except Exception as e:
        print(f"An error occurred:  {e}")
    finally:
        if conn:
            cur.close()
            conn.close()
else:
    print("Failed to connect to the database")
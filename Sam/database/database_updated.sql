-- Step 1: Create the laptops table with memory column
CREATE TABLE laptops (
    model VARCHAR(80) PRIMARY KEY,
    cpu VARCHAR(50),
    brand VARCHAR(50) NOT NULL,
    operatingSystem VARCHAR(50) DEFAULT 'none',
    screenSize VARCHAR(12) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    weight VARCHAR(10) NOT NULL,
    batteryLife VARCHAR(30) NOT NULL,
    FOREIGN KEY(cpu) REFERENCES CPU(model)
);

-- Step 2: Create the CPU table with a unique constraint on 'cpu'
CREATE TABLE CPU (
    model VARCHAR(50) PRIMARY KEY,
    laptop VARCHAR(80) NOT NULL,
    cpu VARCHAR(50),
    brand VARCHAR(50) NOT NULL,
    speed DECIMAL(3, 1),
    FOREIGN KEY (laptop) REFERENCES laptops(model),
    CONSTRAINT unique_cpu UNIQUE (cpu)  -- Add unique constraint to cpu
);

-- Step 3: Create the GPU table, which references both laptops and CPU
CREATE TABLE GPU (
    laptop VARCHAR(80),
    cpu VARCHAR(50),
    model VARCHAR(50) DEFAULT 'none',
    brand VARCHAR(20) DEFAULT 'none',
    FOREIGN KEY (laptop) REFERENCES laptops(model),
    FOREIGN KEY (cpu) REFERENCES CPU(model),
    PRIMARY KEY (laptop, cpu)
);

-- Step 4: Create storage table, referencing both laptops and CPU
CREATE TABLE storage (
    laptop VARCHAR(80),
    cpu VARCHAR(50),
    storage_amount VARCHAR(15) NOT NULL,
    storage_type VARCHAR(15) NOT NULL,
    FOREIGN KEY (laptop) REFERENCES laptops(model),
    FOREIGN KEY (cpu) REFERENCES CPU(model),
    PRIMARY KEY (laptop, cpu)
);

-- Step 5: Create screen table, referencing both laptops and CPU
CREATE TABLE screen (
    laptop VARCHAR(80) NOT NULL,
    cpu VARCHAR(50),
    screen_res VARCHAR(20) NOT NULL,
    refresh VARCHAR(20) NOT NULL,
    touch_screen VARCHAR(10) NOT NULL,
    FOREIGN KEY (laptop) REFERENCES laptops(model),
    FOREIGN KEY (cpu) REFERENCES CPU(model),
    PRIMARY KEY(laptop, cpu, screen_res)
);

-- Step 6: Create features table, referencing both laptops and CPU
CREATE TABLE features (
    laptop VARCHAR(80),
    cpu VARCHAR(50),
    bluetooth VARCHAR(5) DEFAULT 'none',
    num_pad VARCHAR(5) DEFAULT 'none',
    backlit VARCHAR(5) DEFAULT 'none',
    FOREIGN KEY (laptop) REFERENCES laptops(model),
    FOREIGN KEY (cpu) REFERENCES CPU(model),
    PRIMARY KEY(laptop, cpu)
);

-- Step 7: Create ports table, referencing both laptops and CPU
CREATE TABLE ports (
    laptop VARCHAR(80),
    cpu VARCHAR(50),
    hdmi VARCHAR(10) NOT NULL,
    ethernet VARCHAR(10) NOT NULL,
    thunderbolt VARCHAR(10) NOT NULL,
    typec VARCHAR(10) NOT NULL,
    display_port VARCHAR(10) NOT NULL,
    FOREIGN KEY (laptop) REFERENCES laptops(model),
    FOREIGN KEY (cpu) REFERENCES CPU(model),
    PRIMARY KEY(laptop, cpu)
);

-- Step 8: Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    uname VARCHAR(50) NOT NULL,
    phonenum VARCHAR(15) NOT NULL,  -- Changed from 'int' to 'VARCHAR'
    email VARCHAR(50),
    password VARCHAR(512) NOT NULL
);

-- Step 9: Insert users into the users table
INSERT INTO users (uname, phonenum, email, password)
VALUES 
    ('quantumpanda', '02079460958', 'quantum.panda@example.com', 'e3d6b4f5a6b1c2e8f9a0d7b8c6d5e4f3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6'),
    ('StarlightVoyager', '0131490123', 'starlight.voyager@example.com', 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2'),
    ('NeonFalcon', '01614993456', 'neon.falcon@example.com', 'b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3'),
    ('MysticGrizzly', '01214967890', 'mystic.grizzly@example.com', 'c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4'),
    ('CyberPhoenix', '01414962345', 'cyber.phoenix@example.com', 'd4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5');

-- Step 10: Create images table
CREATE TABLE images (
    image BYTEA NOT NULL,  -- binary object to hold image
    laptop_id SERIAL NOT NULL,
    laptop VARCHAR(80),
    PRIMARY KEY (laptop_id),
    FOREIGN KEY (laptop) REFERENCES laptops(model)
);

-- Step 11: Create a view to show user information without actual password
CREATE VIEW user_info AS
SELECT
    uname, 
    phonenum,
    email,
    substring(md5(random()::text) FROM 1 FOR 10) AS fake_password
FROM users;

-- Step 12: Selecting from the user_info view
SELECT * FROM user_info;

-- Step 13: Create a view to show all laptops that have no GPU
CREATE VIEW no_gpu AS
SELECT * FROM GPU
WHERE model = 'none';


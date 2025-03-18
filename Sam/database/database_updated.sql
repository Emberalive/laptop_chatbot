-- Create the laptops table
CREATE TABLE laptops (
    model VARCHAR(80) PRIMARY KEY,
    brand VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    weight VARCHAR(10) NOT NULL,
    battery_life VARCHAR(30) NOT NULL,
    memory_installed VARCHAR(20) NOT NULL,  -- New attribute for RAM size
    operating_system VARCHAR(50) DEFAULT 'none',  -- New attribute for OS
    screen_size VARCHAR(12) NOT NULL  -- New attribute for screen size
);

-- Create the cpu table
CREATE TABLE cpu (
    model VARCHAR(50),
    brand VARCHAR(50),
    laptop_model VARCHAR(80) NOT NULL,
    FOREIGN KEY (laptop_model) REFERENCES laptops(model),
    PRIMARY KEY (model, laptop_model)  -- Fix syntax error
);

-- Create the gpu table
CREATE TABLE gpu (
    model VARCHAR(50),
    brand VARCHAR(50),
    laptop_model VARCHAR(80) NOT NULL,
    FOREIGN KEY (laptop_model) REFERENCES laptops(model),
    PRIMARY KEY (model, laptop_model)
);

-- Create the storage table
CREATE TABLE storage (
    storage_id SERIAL PRIMARY KEY,  -- Only storage_id as the primary key
    laptop_model VARCHAR(80) NOT NULL,
    storage_amount VARCHAR(15) NOT NULL,
    storage_type VARCHAR(15) NOT NULL,
    FOREIGN KEY (laptop_model) REFERENCES laptops(model)
);

-- Create the screen table
CREATE TABLE screen (
    laptop_model VARCHAR(80) NOT NULL,
    screen_resolution VARCHAR(20) NOT NULL,
    refresh_rate VARCHAR(20) NOT NULL,
    touch_screen VARCHAR(10) NOT NULL,
    FOREIGN KEY (laptop_model) REFERENCES laptops(model),
    PRIMARY KEY (laptop_model, screen_resolution)  -- Fix typo (screen_resolution)
);

-- Create the features table
CREATE TABLE features (
    feature_id SERIAL PRIMARY KEY,  -- Unique ID for each feature entry
    laptop_model VARCHAR(80) NOT NULL,
    bluetooth VARCHAR(10) NOT NULL,
    num_pad VARCHAR(10) NOT NULL,
    backlit_keyboard VARCHAR(10) NOT NULL,
    FOREIGN KEY (laptop_model) REFERENCES laptops(model)
);

-- Create the ports table
CREATE TABLE ports (
    port_id SERIAL PRIMARY KEY,  -- Unique ID for each port entry
    laptop_model VARCHAR(80) NOT NULL,
    hdmi VARCHAR(10) NOT NULL,
    ethernet VARCHAR(10) NOT NULL,
    thunderbolt VARCHAR(10) NOT NULL,
    type_c VARCHAR(10) NOT NULL,
    display_port VARCHAR(10) NOT NULL,
    FOREIGN KEY (laptop_model) REFERENCES laptops(model)
);

-- Create the users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(50),
    password VARCHAR(512) NOT NULL
);

-- Create the images table
CREATE TABLE images (
    image_id SERIAL PRIMARY KEY,  -- Unique ID for each image
    laptop_model VARCHAR(80) NOT NULL,
    image BYTEA NOT NULL,
    FOREIGN KEY (laptop_model) REFERENCES laptops(model)
);


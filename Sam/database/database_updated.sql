-- Base tables with no foreign key dependencies
CREATE TABLE laptop_models (
    model_id SERIAL PRIMARY KEY,
    brand VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) UNIQUE NOT NULL,
    image_url TEXT
);

CREATE TABLE processors (
    model VARCHAR(100) PRIMARY KEY,
    brand VARCHAR(50) NOT NULL
);

CREATE TABLE graphics_cards (
    model VARCHAR(100) PRIMARY KEY,
    brand VARCHAR(50) NOT NULL
);

CREATE TABLE storge_types (
    type VARCHAR(20) PRIMARY KEY
);

-- Tables that reference the base tables
CREATE TABLE laptop_configurations (
    config_id SERIAL UNIQUE,
    model_id INTEGER NOT NULL REFERENCES laptop_models(model_id) ON DELETE CASCADE,
    price VARCHAR(25),
    weight VARCHAR(20) ,
    battery_life VARCHAR(30),
    memory_installed VARCHAR(20) NOT NULL,
    operating_system VARCHAR(50),
    processor VARCHAR(100) NOT NULL,
    graphics_card VARCHAR(100) NOT NULL,
    "AMP" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (processor) REFERENCES processors (model),
    FOREIGN KEY (graphics_card) REFERENCES graphics_cards (model),
    PRIMARY KEY(config_id, model_id) 
);

-- Insert data after table exists
INSERT INTO storge_types (type) VALUES ('SSD');
INSERT INTO storge_types (type) VALUES ('HDD');
INSERT INTO storge_types (type) VALUES ('NVME');
INSERT INTO storge_types (type) VALUES ('EMMC');
INSERT INTO storge_types (type) VALUES ('none');

-- Tables that depend on laptop_configurations and storge_types
CREATE TABLE configuration_storage (
    config_id INTEGER NOT NULL,
    storage_type VARCHAR(10) NOT NULL,
    capacity VARCHAR(15) NOT NULL,
    PRIMARY KEY (config_id, storage_type),
    FOREIGN KEY (config_id) REFERENCES laptop_configurations(config_id),
    FOREIGN KEY (storage_type) REFERENCES   storge_types(type)
);

CREATE TABLE features (
    config_id INTEGER PRIMARY KEY,
    backlit_keyboard BOOLEAN DEFAULT FALSE,
    numeric_keyboard BOOLEAN DEFAULT FALSE,
    bluetooth BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (config_id) REFERENCES laptop_configurations(config_id)
);

CREATE TABLE ports (
    config_id INTEGER PRIMARY KEY,
    ethernet BOOLEAN DEFAULT FALSE,
    hdmi BOOLEAN DEFAULT FALSE,
    usb_type_c BOOLEAN DEFAULT FALSE,
    thunderbolt BOOLEAN DEFAULT FALSE,
    display_port BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (config_id) REFERENCES laptop_configurations(config_id)
);

CREATE TABLE screens (
    config_id INTEGER PRIMARY KEY,
    size VARCHAR(12) NOT NULL,
    resolution VARCHAR(20) NOT NULL,
    touchscreen BOOLEAN DEFAULT FALSE,
    refresh_rate VARCHAR(20),
    FOREIGN KEY (config_id) REFERENCES laptop_configurations(config_id)
);
CREATE TABLE users (
username VARCHAR(50) PRIMARY KEY,
password VARCHAR(255),
email VARCHAR(70),
pref_laptop VARCHAR(100),
budget VARCHAR(13)
);
CREATE TABLE pref_laptop (
    username VARCHAR(50),
    config_id SERIAL UNIQUE,
    price VARCHAR(25),
    weight VARCHAR(10) ,
    battery_life VARCHAR(30),
    memory_installed VARCHAR(20) NOT NULL,
    operating_system VARCHAR(50),
    processor VARCHAR(50) NOT NULL,
    graphics_card VARCHAR(50) NOT NULL,
    "AMP" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (processor) REFERENCES processors (model),
    FOREIGN KEY (graphics_card) REFERENCES graphics_cards (model),
    FOREIGN KEY (username) REFERENCES users (username),
    PRIMARY KEY(config_id, username) 
);

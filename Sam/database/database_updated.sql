
// stores basic information
CREATE TABLE laptop_models (
    model_id SERIAL PRIMARY KEY,
    brand VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    image_url TEXT
);

//stores different hardware configurations for each model
CREATE TABLE laptop_configurations (
    config_id SERIAL,
    model_id INTEGER NOT NULL REFERENCES laptop_models(model_id) ON DELETE CASCADE,
    price NUMERIC(10,2),
    weight NUMERIC(5,2) CHECK (weight > 0),
    battery_life VARCHAR(30),
    memory_installed VARCHAR(20) NOT NULL,
    operating_system VARCHAR(50),
    processor VARCHAR(50) NOT NULL,
    graphics_card VARCHAR(50) NOT NULL,AMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (processor) REFERENCES processors (brand),
    FOREIGN KEY (graphics_card) REFERENCES graphics_cards (brand),
    PRIMARY KEY(config_id, model_id) 
);

CREATE TABLE processors (
    model VARCHAR(100)  PRIMARY KEY,
    brand NOT NULLVARCHAR(50) NOT NULL ,
);

CREATE TABLE graphics_cards (
    model VARCHAR(100) PRIMARY KEY ,
    brand NOT NULL NOT NULL,
);

CREATE TABLE storge_types (
    type VARCHAR(20) NOT NULL
);

INSERT INTO storage_types (type) VALUES ('SSD');
INSERT INTO storage_types (type) VALUES ('HDD');
INSERT INTO storage_types (type) VALUES ('NVMe');
INSERT INTO storage_types (type) VALUES ('eMMC');


CREATE TABLE configuration_storage (
    config_id INTEGER NOT NULL REFERENCES laptop_configurations(config_id) ON DELETE CASCADE,
    storage_type VARCHAR(10) NOT NULL REFERENCES storge_types(type) ON DELETE CASCADE,
    capacity VARCHAR(15) NOT NULL,
    PRIMARY KEY (config_id, storage_type)
);

CREATE TABLE features (
    config_id INTEGER PRIMARY KEY REFERENCES laptop_configurations(config_id) ON DELETE CASCADE,
    backlit_keyboard BOOLEAN DEFAULT FALSE,
    numeric_keyboard BOOLEAN DEFAULT FALSE,
    bluetooth BOOLEAN DEFAULT FALSE
);

CREATE TABLE ports (
    config_id INTEGER PRIMARY KEY REFERENCES laptop_configurations(config_id) ON DELETE CASCADE,
    ethernet BOOLEAN DEFAULT FALSE,
    hdmi BOOLEAN DEFAULT FALSE,
    usb_type_c BOOLEAN DEFAULT FALSE,
    thunderbolt BOOLEAN DEFAULT FALSE,
    display_port BOOLEAN DEFAULT FALSE
);

CREATE TABLE screens (
    config_id INTEGER PRIMARY KEY REFERENCES laptop_configurations(config_id) ON DELETE CASCADE,
    size VARCHAR(12) NOT NULL,
    resolution VARCHAR(20) NOT NULL,
    touchscreen BOOLEAN DEFAULT FALSE,
    refresh_rate VARCHAR(20)
);





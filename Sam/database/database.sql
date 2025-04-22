CREATE TABLE laptop_models (
    model_id SERIAL PRIMARY KEY,
    brand VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    image_url TEXT
);

CREATE TABLE laptop_configurations (
    config_id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES laptop_models(model_id) ON DELETE CASCADE,
    price NUMERIC(10,2),
    weight NUMERIC(5,2) CHECK (weight > 0),
    battery_life VARCHAR(30),
    memory_installed VARCHAR(20) NOT NULL,
    operating_system VARCHAR(50),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE processors (
    processor_id SERIAL PRIMARY KEY,
    brand VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL
);

CREATE TABLE graphics_cards (
    gpu_id SERIAL PRIMARY KEY,
    brand VARCHAR(50),
    model VARCHAR(100) NOT NULL
);

CREATE TABLE storage (
    storage_id SERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL CHECK (type IN ('SSD', 'HDD', 'NVMe', 'eMMC'))
);

CREATE TABLE configuration_processors (
    config_id INTEGER NOT NULL REFERENCES laptop_configurations(config_id) ON DELETE CASCADE,
    processor_id INTEGER NOT NULL REFERENCES processors(processor_id),
    PRIMARY KEY (config_id, processor_id)
);

CREATE TABLE configuration_gpus (
    config_id INTEGER NOT NULL REFERENCES laptop_configurations(config_id) ON DELETE CASCADE,
    gpu_id INTEGER NOT NULL REFERENCES graphics_cards(gpu_id),
    PRIMARY KEY (config_id, gpu_id)
);

CREATE TABLE configuration_storage (
    config_id INTEGER NOT NULL REFERENCES laptop_configurations(config_id) ON DELETE CASCADE,
    storage_id INTEGER NOT NULL REFERENCES storage_types(storage_id),
    capacity VARCHAR(15) NOT NULL,
    PRIMARY KEY (config_id, storage_id, capacity)
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
    matte BOOLEAN DEFAULT FALSE,
    refresh_rate VARCHAR(20)
);



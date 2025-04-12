CREATE TABLE laptops (
    model character varying(80) NOT NULL,
    brand character varying(50) NOT NULL,
    price character varying NOT NULL,
    weight character varying(10) NOT NULL,
    battery_life character varying(30) NOT NULL,  -- Keep battery_life as is
    memory_installed character varying(20) NOT NULL,
    operating_system character varying(50) DEFAULT 'none'::character varying,
    screen_size character varying(12) NOT NULL,
    PRIMARY KEY (model, weight, screen_size, battery_life, memory_installed)  -- Updated primary key to include battery_life
);

-- cpu table update
CREATE TABLE cpu (
    model character varying(50) NOT NULL,
    brand character varying(50),
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    laptop_battery_life character varying(30) NOT NULL,  -- Added battery_life
    laptop_memory character varying(20) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory) 
        REFERENCES laptops(model, weight, screen_size, battery_life, memory_installed),
    PRIMARY KEY (model, laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory)  -- Updated primary key
);

-- gpu table update
CREATE TABLE gpu (
    model character varying(50) NOT NULL,
    brand character varying(50),
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    laptop_battery_life character varying(30) NOT NULL,  -- Added battery_life
    laptop_memory character varying(20) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory) 
        REFERENCES laptops(model, weight, screen_size, battery_life, memory_installed),
    PRIMARY KEY (model, laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory)  -- Updated primary key
);

-- features table update
CREATE TABLE features (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    laptop_battery_life character varying(30) NOT NULL,  -- Added battery_life
    bluetooth character varying(10) NOT NULL,
    num_pad character varying(10) NOT NULL,
    backlit_keyboard character varying(10) NOT NULL,
    laptop_memory character varying(20) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory) 
        REFERENCES laptops(model, weight, screen_size, battery_life, memory_installed),
    PRIMARY KEY (laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory)  -- Updated primary key
);

-- ports table update
CREATE TABLE ports (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    laptop_battery_life character varying(30) NOT NULL,  -- Added battery_life
    hdmi character varying(10) NOT NULL,
    ethernet character varying(10) NOT NULL,
    thunderbolt character varying(10) NOT NULL,
    type_c character varying(10) NOT NULL,
    display_port character varying(10) NOT NULL,
    laptop_memory character varying(20) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory) 
        REFERENCES laptops(model, weight, screen_size, battery_life, memory_installed),
    PRIMARY KEY (laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory)  -- Updated primary key
);

-- screen table update
CREATE TABLE screen (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    laptop_battery_life character varying(30) NOT NULL,  -- Added battery_life
    screen_resolution character varying(20) NOT NULL,
    refresh_rate character varying(20) NOT NULL,
    touch_screen character varying(10) NOT NULL,
    laptop_memory character varying(20) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory) 
        REFERENCES laptops(model, weight, screen_size, battery_life, memory_installed),
    PRIMARY KEY (laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory)  -- Updated primary key
);

-- storage table update
CREATE TABLE storage (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    laptop_battery_life character varying(30) NOT NULL,  -- Added battery_life
    storage_amount character varying(15) NOT NULL,
    storage_type character varying(15) NOT NULL,
    laptop_memory character varying(20) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory) 
        REFERENCES laptops(model, weight, screen_size, battery_life, memory_installed),
    PRIMARY KEY (laptop_model, laptop_weight, laptop_screen, laptop_battery_life, laptop_memory)  -- Updated primary key
);



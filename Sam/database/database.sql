CREATE TABLE laptops (
    model character varying(80) NOT NULL,
    brand character varying(50) NOT NULL,
    price character varying NOT NULL,
    weight character varying(10) NOT NULL,
    battery_life character varying(30) NOT NULL,
    memory_installed character varying(20) NOT NULL,
    operating_system character varying(50) DEFAULT 'none'::character varying,
    screen_size character varying(12) NOT NULL,
    PRIMARY KEY (model, weight, screen_size)
);

CREATE TABLE cpu (
    model character varying(50) NOT NULL,
    brand character varying(50),
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen) REFERENCES laptops(model, weight, screen_size),
    PRIMARY KEY (model, laptop_model, laptop_weight, laptop_screen)
);

CREATE TABLE gpu (
    model character varying(50) NOT NULL,
    brand character varying(50),
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen) REFERENCES laptops(model, weight, screen_size),
    PRIMARY KEY (model, laptop_model, laptop_weight, laptop_screen)
);

CREATE TABLE features (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    bluetooth character varying(10) NOT NULL,
    num_pad character varying(10) NOT NULL,
    backlit_keyboard character varying(10) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen) REFERENCES laptops(model, weight, screen_size),
    PRIMARY KEY (laptop_model, laptop_weight, laptop_screen)
);

CREATE TABLE ports (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    hdmi character varying(10) NOT NULL,
    ethernet character varying(10) NOT NULL,
    thunderbolt character varying(10) NOT NULL,
    type_c character varying(10) NOT NULL,
    display_port character varying(10) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen) REFERENCES laptops(model, weight, screen_size),
    PRIMARY KEY (laptop_model, laptop_weight, laptop_screen)
);

CREATE TABLE screen (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    screen_resolution character varying(20) NOT NULL,
    refresh_rate character varying(20) NOT NULL,
    touch_screen character varying(10) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen) REFERENCES laptops(model, weight, screen_size),
    PRIMARY KEY (laptop_model, laptop_weight, laptop_screen)
);

CREATE TABLE storage (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL,
    laptop_screen character varying(12) NOT NULL,
    storage_amount character varying(15) NOT NULL,
    storage_type character varying(15) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight, laptop_screen) REFERENCES laptops(model, weight, screen_size),
    PRIMARY KEY (laptop_model, laptop_weight, laptop_screen)
);

CREATE TABLE users (
    id integer NOT NULL,
    username character varying(50) PRIMARY KEY,
    phone_number character varying(20) NOT NULL,
    email character varying(50),
    password character varying(512) NOT NULL
);


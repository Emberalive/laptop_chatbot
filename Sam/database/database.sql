CREATE TABLE laptops (
    model character varying(80) NOT NULL,
    brand character varying(50) NOT NULL,
    price character varying NOT NULL,
    weight character varying(10) NOT NULL,
    battery_life character varying(30) NOT NULL,
    memory_installed character varying(20) NOT NULL,
    operating_system character varying(50) DEFAULT 'none'::character varying,
    screen_size character varying(12) NOT NULL,
    PRIMARY KEY (model, weight)
);

CREATE TABLE cpu (
    model character varying(50) NOT NULL,
    brand character varying(50),
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL, -- Added weight for the composite foreign key
    FOREIGN KEY (laptop_model, laptop_weight) REFERENCES laptops(model, weight),
    PRIMARY KEY (model, laptop_model, laptop_weight)
);

CREATE TABLE gpu (
    model character varying(50) NOT NULL,
    brand character varying(50),
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL, -- Added weight for the composite foreign key
    FOREIGN KEY (laptop_model, laptop_weight) REFERENCES laptops(model, weight),
    PRIMARY KEY (model, laptop_model, laptop_weight)
);

CREATE TABLE features (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL, -- Added weight for the composite foreign key
    bluetooth character varying(10) NOT NULL,
    num_pad character varying(10) NOT NULL,
    backlit_keyboard character varying(10) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight) REFERENCES laptops(model, weight),
    PRIMARY KEY (laptop_model, laptop_weight)
);

CREATE TABLE ports (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL, -- Added weight for the composite foreign key
    hdmi character varying(10) NOT NULL,
    ethernet character varying(10) NOT NULL,
    thunderbolt character varying(10) NOT NULL,
    type_c character varying(10) NOT NULL,
    display_port character varying(10) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight) REFERENCES laptops(model, weight),
    PRIMARY KEY (laptop_model, laptop_weight)
);

CREATE TABLE screen (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL, -- Added weight for the composite foreign key
    screen_resolution character varying(20) NOT NULL,
    refresh_rate character varying(20) NOT NULL,
    touch_screen character varying(10) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight) REFERENCES laptops(model, weight),
    PRIMARY KEY (laptop_model, laptop_weight)
);

CREATE TABLE storage (
    laptop_model character varying(80) NOT NULL,
    laptop_weight character varying(10) NOT NULL, -- Added weight for the composite foreign key
    storage_amount character varying(15) NOT NULL,
    storage_type character varying(15) NOT NULL,
    FOREIGN KEY (laptop_model, laptop_weight) REFERENCES laptops(model, weight),
    PRIMARY KEY (laptop_model, laptop_weight)
);

CREATE TABLE users (
    id integer NOT NULL,
    username character varying(50) PRIMARY KEY,
    phone_number character varying(20) NOT NULL,
    email character varying(50),
    password character varying(512) NOT NULL
);


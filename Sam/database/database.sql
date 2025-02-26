CREATE TABLE laptops (
id SERIAL PRIMARY KEY,
model VARCHAR(80),
brand VARCHAR(50) NOT NULL,
operatingSystem VARCHAR default 'none',
screenSize  VARCHAR (12) NOT NULL,
price DECIMAL(10, 2) NOT NULL,
weight VARCHAR(10) NOT NULL,
batteryLife VARCHAR (30)NOT NULL
);

ALTER TABLE laptops
ADD COLUMN memory VARCHAR(20) NOT NULL;

CREATE TABLE CPU (
laptop_id SERIAL NOT NULL,
laptop VARCHAR(80) NOT NULL,
model VARCHAR(50),
brand VARCHAR(50) NOT NULL,
speed DECIMAL(3, 1) ,
FOREIGN KEY (laptop_id) REFERENCES laptops(id),
PRIMARY KEY (model, laptop_id)
);

ALTER TABLE cpu 
DROP COLUMN speed;

CREATE TABLE GPU (
laptop_id SERIAL NOT NULL,
laptop VARCHAR(80),
model VARCHAR(30),
brand VARCHAR(20) NOT NULL,
FOREIGN KEY (laptop_id) REFERENCES laptops(id),
PRIMARY KEY (laptop_id, model)
);

CREATE TABLE memory (
laptop_id SERIAL NOT NULL,
laptop VARCHAR(80) PRIMARY KEY,
storage int NOT NULL,
FOREIGN KEY (laptop_id) REFERENCES laptops(id)
);

 CREATE TABLE storage (
 laptop_id SERIAL NOT NULL,
 storage_id SERIAL PRIMARY KEY, --this is so that there can be multiple storage types in one laptop
laptop VARCHAR(80),
 amount int NOT NULL,
 type VARCHAR(30) NOT NULL,
 FOREIGN KEY (laptop_id) REFERENCES laptops(id)
 );
 
 CREATE TABLE users (
id int PRIMARY KEY,
uname VARCHAR(50) NOT NULL,
phonenum int NOT NULL,
email VARCHAR(50) NULL,
password VARCHAR(200) NOT NULL
);

CREATE TABLE images (
image BYTEA NOT NULL,  -- creates a binary object to hold the image
laptop_id SERIAL NOT NULL,
laptop VARCHAR(80) PRIMARY KEY,
FOREIGN KEY (laptop_id) REFERENCES laptops(id)
);

CREATE TABLE screen (
laptop_id SERIAL NOT NULL,
laptop VARCHAR(80) PRIMARY KEY,
size int NOT NULL,
screen_res VARCHAR(20) NOT NULL,
refresh VARCHAR(20) NOT NULL,
touch_screen VARCHAR(10) NOT NULL,
FOREIGN KEY (laptop_id) REFERENCES laptops(id)
);

CREATE TABLE features (
laptop_id SERIAL PRIMARY KEY,
laptop VARCHAR(80),
bluetooth VARCHAR(5) default 'none',
num_pad VARCHAR(5) default 'none',
backlit VARCHAR(5) default 'none'
);

CREATE TABLE ports(
laptop_id SERIAL NOT NULL,
laptop VARCHAR(80) PRIMARY KEY,
hdmi VARCHAR(5) NOT NULL,
ethernet VARCHAR(5) NOT NULL,
thunderbolt VARCHAR(5) NOT NULL,
typec VARCHAR(5) NOT NULL,
display_port VARCHAR(5) NOT NULL,
FOREIGN KEY (laptop_id) REFERENCES laptops(id)
);

ALTER TABLE users
ALTER COLUMN uname TYPE VARCHAR(20);

ALTER TABLE users
ALTER COLUMN password TYPE VARCHAR(512);

ALTER TABLE users DROP COLUMN id;

ALTER TABLE users 
ADD COLUMN id SERIAL PRIMARY KEY; 

INSERT INTO users (uname, phonenum, email, password)
VALUES 
-- password BlueSky$2023!
    ('quantumpanda', '02079460958', 'quantum.panda@example.com', 'e3d6b4f5a6b1c2e8f9a0d7b8c6d5e4f3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6'),
	-- password Tiger@Moon99
    ('StarlightVoyager', '0131490123', 'starlight.voyager@example.com', 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2'),
	-- password Ocean#Wave123
    ('NeonFalcon', '01614993456', 'neon.falcon@example.com', 'b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3'),
	-- password Fire&Ice_456
    ('MysticGrizzly', '01214967890', 'mystic.grizzly@example.com', 'c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4'),
	-- password Star^Night789
    ('CyberPhoenix', '01414962345', 'cyber.phoenix@example.com', 'd4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5');

-- this view shows the users information without showing the actual password hash, by making a fake password
CREATE VIEW user_info AS
SELECT
	uname, 
	phonenum,
	email,
	substring(md5(random()::text) FROM 1 FOR 10) AS fake_password
	FROM users;

-- selects the view
SELECT * FROM user_info;

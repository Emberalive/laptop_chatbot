CREATE TABLE laptops (
model VARCHAR(80) PRIMARY KEY,
brand VARCHAR(50) NOT NULL,
operatingSystem VARCHAR default 'none',
screenSize DECIMAL(3, 1) NOT NULL,
price DECIMAL(10, 2) NOT NULL,
weight VARCHAR(10) NOT NULL,
batteryLife VARCHAR(10) NOT NULL
);

CREATE TABLE CPU (
laptop VARCHAR(80) NOT NULL,
model VARCHAR(20) PRIMARY KEY,
brand VARCHAR(20) NOT NULL,
speed DECIMAL(3, 1) NOT NULL,
FOREIGN KEY (laptop) REFERENCES laptops(model)
);

CREATE TABLE GPU (
laptop VARCHAR(80),
model VARCHAR(30),
brand VARCHAR(20) NOT NULL,
FOREIGN KEY (laptop) REFERENCES laptops(model),
PRIMARY KEY (laptop, model)
);

CREATE TABLE memory (
laptop VARCHAR(80) PRIMARY KEY,
storage int NOT NULL,
FOREIGN KEY (laptop) REFERENCES laptops(model)
);

 CREATE TABLE storage (
 id SERIAL PRIMARY KEY, --this is so that there can be multiple storage types in one laptop
laptop VARCHAR(80),
 amount int NOT NULL,
 type VARCHAR(30) NOT NULL,
 FOREIGN KEY (laptop) REFERENCES laptops(model)
 );
 
 CREATE TABLE users (
id int PRIMARY KEY,
uname VARCHAR(50) NOT NULL,
phonenum int NOT NULL,
email VARCHAR(50) NULL
);


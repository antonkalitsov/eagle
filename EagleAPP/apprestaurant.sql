CREATE DATABASE IF NOT EXISTS apprestaurant;
USE apprestaurant;

-- Таблица с потребители
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    role ENUM('client', 'employee', 'admin') NOT NULL
);

-- Меню с ястия и цени
CREATE TABLE IF NOT EXISTS menu (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

-- Основна таблица с поръчки
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Подробности за всяка поръчка (артикули)
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Таблица за завършени поръчки от служители
CREATE TABLE IF NOT EXISTS finished_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    employee_id INT NOT NULL,
    finished_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (employee_id) REFERENCES users(id)
);



ALTER TABLE orders ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE orders ADD COLUMN accepted_by INT DEFAULT NULL;
ALTER TABLE menu ADD COLUMN category VARCHAR(100);

ALTER TABLE orders
ADD COLUMN status ENUM('pending', 'delivered') DEFAULT 'pending' AFTER total_price;

-- Create a table for restaurants
CREATE TABLE IF NOT EXISTS restaurants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL
);

-- Link the menu table to restaurants
ALTER TABLE menu ADD COLUMN restaurant_id INT;


ALTER TABLE orders ADD COLUMN restaurant_id INT NOT NULL;


-- Add a client_address column to orders for delivery
ALTER TABLE orders ADD COLUMN client_address VARCHAR(255) NOT NULL;


ALTER TABLE menu ADD CONSTRAINT fk_restaurant_id
FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
ON DELETE CASCADE;



ALTER TABLE finished_orders ADD COLUMN bonus INT DEFAULT 0;

CREATE TABLE bonus_criteria (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orders_required INT NOT NULL DEFAULT 5,
    bonus_amount INT NOT NULL DEFAULT 50
);
INSERT INTO bonus_criteria (orders_required, bonus_amount) VALUES (5, 50);

import sqlite3
import hashlib
from datetime import datetime
import os
import random

DB_PATH = "house_price_app.db"
LOCATIONS = ['Downtown', 'Suburbs', 'Uptown', 'Rural']

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Login Logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create Prediction Logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            area REAL,
            bedrooms INTEGER,
            bathrooms INTEGER,
            age INTEGER,
            location TEXT,
            model_used TEXT,
            predicted_price REAL,
            prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create Plots Inventory
    c.execute('''
        CREATE TABLE IF NOT EXISTS plots_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            size_sqft REAL,
            price REAL,
            status TEXT DEFAULT 'Available'
        )
    ''')
    
    # Create Houses Inventory
    c.execute('''
        CREATE TABLE IF NOT EXISTS houses_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            bedrooms INTEGER,
            bathrooms INTEGER,
            area_sqft REAL,
            price REAL,
            status TEXT DEFAULT 'Available'
        )
    ''')
    
    conn.commit()
    conn.close()
    
    seed_inventory()

def seed_inventory():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if plots empty
    c.execute('SELECT COUNT(*) FROM plots_inventory')
    if c.fetchone()[0] == 0:
        for _ in range(20):
            loc = random.choice(LOCATIONS)
            size = random.randint(1000, 10000)
            price = size * random.randint(50, 150)
            c.execute('INSERT INTO plots_inventory (location, size_sqft, price) VALUES (?, ?, ?)', (loc, size, price))
            
    # Check if houses empty
    c.execute('SELECT COUNT(*) FROM houses_inventory')
    if c.fetchone()[0] == 0:
        for _ in range(20):
            loc = random.choice(LOCATIONS)
            area = random.randint(1000, 5000)
            beds = random.randint(2, 5)
            baths = random.randint(1, 4)
            price = (area * 150) + (beds * 20000) + (baths * 15000) + random.randint(-20000, 20000)
            c.execute('INSERT INTO houses_inventory (location, bedrooms, bathrooms, area_sqft, price) VALUES (?, ?, ?, ?, ?)', 
                      (loc, beds, baths, area, price))
            
    conn.commit()
    conn.close()

def get_available_plots():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, location, size_sqft, price, status FROM plots_inventory WHERE status = "Available"')
    plots = c.fetchall()
    conn.close()
    return plots

def reserve_plot(plot_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE plots_inventory SET status = "Reserved" WHERE id = ?', (plot_id,))
    conn.commit()
    conn.close()

def get_available_houses():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, location, bedrooms, bathrooms, area_sqft, price, status FROM houses_inventory WHERE status = "Available"')
    houses = c.fetchall()
    conn.close()
    return houses

def reserve_house(house_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE houses_inventory SET status = "Reserved" WHERE id = ?', (house_id,))
    conn.commit()
    conn.close()

def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                  (username, _hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username = ? AND password_hash = ?', 
              (username, _hash_password(password)))
    user = c.fetchone()
    conn.close()
    if user:
        return user[0]
    return None

def log_login(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO login_logs (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

def log_prediction(user_id, area, bedrooms, bathrooms, age, location, model_used, predicted_price):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO prediction_logs 
        (user_id, area, bedrooms, bathrooms, age, location, model_used, predicted_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, area, bedrooms, bathrooms, age, location, model_used, predicted_price))
    conn.commit()
    conn.close()

def get_prediction_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT u.username, p.area, p.bedrooms, p.bathrooms, p.age, p.location, p.model_used, p.predicted_price, p.prediction_time 
        FROM prediction_logs p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.prediction_time DESC
    ''')
    logs = c.fetchall()
    conn.close()
    return logs

def get_login_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT u.username, l.login_time 
        FROM login_logs l
        JOIN users u ON l.user_id = u.id
        ORDER BY l.login_time DESC
    ''')
    logs = c.fetchall()
    conn.close()
    return logs

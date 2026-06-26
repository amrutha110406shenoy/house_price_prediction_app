import sqlite3
import hashlib
from datetime import datetime
import os

DB_PATH = "house_price_app.db"

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

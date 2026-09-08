import sqlite3
import json
from datetime import datetime, timedelta

DB_NAME = "bot.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            join_date TEXT,
            credits INTEGER DEFAULT 150,
            premium_expiry TEXT,
            is_premium BOOLEAN DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS gate_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS gates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT,
            command TEXT,
            sites TEXT,                -- JSON array of site URLs
            extra_info TEXT,
            FOREIGN KEY(category_id) REFERENCES gate_categories(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            duration_days INTEGER,
            price_usd REAL,
            description TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan_id INTEGER,
            amount REAL,
            currency TEXT,
            tx_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(plan_id) REFERENCES plans(id)
        )
    ''')
    # Add default categories if empty
    default_categories = ["Auth", "Mass", "Charge", "Hitter"]
    for cat in default_categories:
        c.execute("INSERT OR IGNORE INTO gate_categories (name) VALUES (?)", (cat,))
    # Add default plans if empty
    c.execute("SELECT COUNT(*) FROM plans")
    if c.fetchone()[0] == 0:
        default_plans = [
            ("Lite", 2, 4.0, "2 Days Access"),
            ("Core", 7, 8.0, "7 Days Access"),
            ("Elite", 15, 14.0, "15 Days Access"),
            ("Root", 30, 27.0, "30 Days Access"),
        ]
        c.executemany("INSERT INTO plans (name, duration_days, price_usd, description) VALUES (?,?,?,?)", default_plans)
    conn.commit()
    conn.close()

# ---- User functions ----
def add_user(user_id, first_name, username):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO users (user_id, first_name, username, join_date)
        VALUES (?, ?, ?, ?)
    ''', (user_id, first_name, username, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "first_name": row[1],
            "username": row[2],
            "join_date": row[3],
            "credits": row[4],
            "premium_expiry": row[5],
            "is_premium": bool(row[6])
        }
    return None

def update_user_credits(user_id, credits):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET credits = ? WHERE user_id = ?', (credits, user_id))
    conn.commit()
    conn.close()

def set_premium(user_id, days):
    expiry = (datetime.now() + timedelta(days=days)).isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET premium_expiry = ?, is_premium = 1 WHERE user_id = ?', (expiry, user_id))
    conn.commit()
    conn.close()

def is_premium(user_id):
    user = get_user(user_id)
    if not user or not user["is_premium"]:
        return False
    expiry = datetime.fromisoformat(user["premium_expiry"])
    return expiry > datetime.now()

def get_credits(user_id):
    user = get_user(user_id)
    return user["credits"] if user else 0

def deduct_credits(user_id, amount=1):
    credits = get_credits(user_id)
    if credits >= amount:
        update_user_credits(user_id, credits - amount)
        return True
    return False

def get_all_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

# ---- Gate Category functions ----
def get_categories():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name FROM gate_categories')
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1]} for r in rows]

def add_category(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO gate_categories (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()

def delete_category(cat_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM gate_categories WHERE id = ?', (cat_id,))
    c.execute('DELETE FROM gates WHERE category_id = ?', (cat_id,))
    conn.commit()
    conn.close()

def get_category_id_by_name(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id FROM gate_categories WHERE name = ?', (name,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

# ---- Gate functions ----
def add_gate(category_id, name, command, sites=None, extra_info=""):
    sites_json = json.dumps(sites or [])
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO gates (category_id, name, command, sites, extra_info)
        VALUES (?, ?, ?, ?, ?)
    ''', (category_id, name, command, sites_json, extra_info))
    conn.commit()
    conn.close()

def get_gates_by_category(category_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, command, sites, extra_info FROM gates WHERE category_id = ?', (category_id,))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "command": r[2], "sites": json.loads(r[3]), "extra_info": r[4]} for r in rows]

def get_gate_by_command(command):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, category_id, name, command, sites, extra_info FROM gates WHERE command = ?', (command,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "category_id": row[1], "name": row[2], "command": row[3], "sites": json.loads(row[4]), "extra_info": row[5]}
    return None

def get_all_gates():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, category_id, name, command, sites, extra_info FROM gates')
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "category_id": r[1], "name": r[2], "command": r[3], "sites": json.loads(r[4]), "extra_info": r[5]} for r in rows]

def delete_gate(gate_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM gates WHERE id = ?', (gate_id,))
    conn.commit()
    conn.close()

# ---- Plan functions ----
def get_all_plans():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, duration_days, price_usd, description FROM plans')
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "duration": r[2], "price": r[3], "description": r[4]} for r in rows]

def get_plan(plan_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, duration_days, price_usd, description FROM plans WHERE id = ?', (plan_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "duration": row[2], "price": row[3], "description": row[4]}
    return None

def add_plan(name, duration, price, description):
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO plans (name, duration_days, price_usd, description) VALUES (?,?,?,?)', (name, duration, price, description))
    conn.commit()
    conn.close()

def delete_plan(plan_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM plans WHERE id = ?', (plan_id,))
    conn.commit()
    conn.close()

# ---- Payment functions ----
def add_payment(user_id, plan_id, amount, currency, tx_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO payments (user_id, plan_id, amount, currency, tx_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'pending', ?)
    ''', (user_id, plan_id, amount, currency, tx_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def update_payment_status(tx_id, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE payments SET status = ? WHERE tx_id = ?', (status, tx_id))
    conn.commit()
    conn.close()

def get_payment_by_tx(tx_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, user_id, plan_id, amount, currency, status FROM payments WHERE tx_id = ?', (tx_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "user_id": row[1], "plan_id": row[2], "amount": row[3], "currency": row[4], "status": row[5]}
    return None

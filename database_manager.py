import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path="/root/Pr1/database/hosting.db"):
        # التأكد من وجود المجلد قبل إنشاء قاعدة البيانات
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                is_admin INTEGER DEFAULT 0,
                is_blocked INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Bots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bots (
                user_id INTEGER PRIMARY KEY,
                process_id INTEGER,
                main_file TEXT,
                status TEXT DEFAULT 'stopped',
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        self.conn.commit()

    def add_user(self, user_id, username, is_admin=0):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username, is_admin) VALUES (?, ?, ?)', (user_id, username, is_admin))
        self.conn.commit()

    def is_blocked(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_blocked FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False

    def is_admin(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] == 1 if result else False

    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT user_id, username FROM users')
        return cursor.fetchall()

    def update_block_status(self, user_id, status):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = ? WHERE user_id = ?', (1 if status else 0, user_id))
        self.conn.commit()

    def set_admin(self, user_id, status):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_admin = ? WHERE user_id = ?', (1 if status else 0, user_id))
        self.conn.commit()

    def update_bot_status(self, user_id, process_id, main_file, status):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO bots (user_id, process_id, main_file, status)
            VALUES (?, ?, ?, ?)
        ''', (user_id, process_id, main_file, status))
        self.conn.commit()

    def get_bot_info(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT process_id, main_file, status FROM bots WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

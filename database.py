import sqlite3
import threading

class Database:
    def __init__(self, db_file="qotil.db"):
        self.db_file = db_file
        self.local = threading.local()
        self.create_tables()

    def get_conn(self):
        if not hasattr(self.local, "conn"):
            self.local.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        return self.local.conn

    def get_cursor(self):
        return self.get_conn().cursor()

    def create_tables(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                name TEXT,
                balance INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def add_user(self, user_id, username, name):
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username, name) VALUES (?, ?, ?)', (user_id, username, name))
        conn.commit()

    def get_user(self, user_id):
        cursor = self.get_cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

    def update_stats(self, user_id, win=False):
        conn = self.get_conn()
        cursor = conn.cursor()
        if win:
            cursor.execute('UPDATE users SET games_played = games_played + 1, wins = wins + 1 WHERE user_id = ?', (user_id,))
        else:
            cursor.execute('UPDATE users SET games_played = games_played + 1 WHERE user_id = ?', (user_id,))
        conn.commit()

    def set_premium(self, user_id, status=True):
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_premium = ? WHERE user_id = ?', (status, user_id))
        conn.commit()

db = Database()

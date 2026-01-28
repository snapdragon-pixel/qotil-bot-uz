import sqlite3

class Database:
    def __init__(self, db_file="qotil.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
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
        self.conn.commit()

    def add_user(self, user_id, username, name):
        self.cursor.execute('INSERT OR IGNORE INTO users (user_id, username, name) VALUES (?, ?, ?)', (user_id, username, name))
        self.conn.commit()

    def get_user(self, user_id):
        self.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return self.cursor.fetchone()

    def update_stats(self, user_id, win=False):
        if win:
            self.cursor.execute('UPDATE users SET games_played = games_played + 1, wins = wins + 1 WHERE user_id = ?', (user_id,))
        else:
            self.cursor.execute('UPDATE users SET games_played = games_played + 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def set_premium(self, user_id, status=True):
        self.cursor.execute('UPDATE users SET is_premium = ? WHERE user_id = ?', (status, user_id))
        self.conn.commit()

db = Database()

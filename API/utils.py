import sqlite3
import hashlib 

class DataBase :
    def __init__(self, path: str) :
        self.connect = sqlite3.connect(path)
        self.connect.row_factory = sqlite3.Row
        self.cursor = self.connect.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_site (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                email              TEXT NOT NULL UNIQUE,
                password_hash      TEXT NOT NULL,
                created            TEXT DEFAULT CURRENT_TIMESTAMP,
                agreement_accepted TEXT DEFAULT CURRENT_TIMESTAMP,
                counts_url         INTEGER DEFAULT 0,
                data_pay           TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_tg (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                id_tg              INTEGER NOT NULL UNIQUE,
                agreement_accepted TEXT DEFAULT CURRENT_TIMESTAMP,
                counts_url         INTEGER DEFAULT 0,
                data_pay           TEXT
            )
        ''')
        self.connect.commit()

    def register_site(self, email: str, password: str) -> int :
        """
        Status code:
        0 - Success
        1 - Email is bussy
        """
        try :
            self.cursor.execute('''
                INSERT INTO users_site (email, password_hash)
                VALUES (?, ?)
            ''', (email.lower().strip(), hashlib.sha256(password.encode()).hexdigest()))
            self.connect.commit()
            return 0
        except sqlite3.IntegrityError :
            return 1
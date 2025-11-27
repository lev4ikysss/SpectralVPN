import sqlite3
import pandas
import datetime
import hashlib
import json

class DataBase :
    def __init__(self, path: str) :
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

        self.cur.execute("""
                            CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                email TEXT NOT NULL UNIQUE,
                                pass_hash TEXT NOT NULL,
                                register TEXT NOT NULL,
                                urls TEXT DEFAULT "",
                                payment TEXT DEFAULT ""
                                )
                        """)
        
        self.con.commit()

    def read_table(self, sql_command: str, params=None) -> dict :
        if params == None :
            params = ()
        return json.loads(pandas.read_sql(sql_command, self.con, params=params).to_json())
    
    def get_hash(text: str) :
        return hashlib.sha256(text.encode()).hexdigest()
    
    def registration(self, email: str, passwd: str) :
        """
            0 - Success
            1 - Email is busy
        """
        date = datetime.datetime.now()
        try :
            self.cur.execute("""
                                INSERT INTO users (email, pass_hash, register)
                                VALUES (?, ?, ?)
                            """, (email, self.get_hash(passwd), f"{date.day}-{date.month}-{date.year} {date.hour}:{date.minute}:{date.second}"))
            self.con.commit()
        except :
            return {"code": 1}
        data = self.read_table("""
                                SELECT id FROM users
                                WHERE email = ?
                               """, (email))
        return {"code": 0, "data": {"id": data["id"]["0"], "email": email}}
        
    def login(self, email: str, passwd: str) :
        """
        0 - Success
        1 - Incorrect email or password
        """
        data = self.read_table("""
                                    SELECT id, urls, payment FROM users
                                    WHERE email = ? AND pass_hash = ?
                                """, (email, self.get_hash(passwd)))
        if data["id"] == {} :
            return {"code": 1}
        else :
            return {"code": 0, "data": {"id": data["id"]["0"], "email": email, "urls": data["urls"]["0"], "payment": data["payment"]["0"]}}
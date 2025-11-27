import sqlite3
import pandas
import datetime
import hashlib

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
                                urls TEXT DEFAULT ""
                                )
                        """)
        
        self.con.commit()

    def read_table(self, sql_command: str) -> dict :
        return pandas.read_sql(sql_command, self.con).to_json()
    
    def registration(self, email: str, passwd: str) :
        """
            0 - Success
            1 - Email is busy
        """
        date = datetime.datetime.now()
        try :
            self.cur.execute(f"""
                                INSERT INTO users (email, pass_hash, register)
                                VALUES ({email} {hashlib.sha256(passwd.encode()).hexdigest()} {date.day}-{date.month}-{date.year}_{date.hour}:{date.minute}:{date.second})
                            """)
        except :
            return {"code": 1}
        self.con.commit()
        data = self.read_table(f"""
                                SELECT id FROM users
                                WHERE email = {email}
                               """)
        return {"code": 0, "data": {"id": data["id"]["0"], "email": email}}
        
    
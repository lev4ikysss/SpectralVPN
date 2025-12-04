import sqlite3
import pandas
import py3xui
import datetime
import hashlib
import json
import uuid

class API :
    def __init__(self, path: str, host: str, username: str, passwd: str, inbaund_id: int, inbaund_url: str, inbaund_port: str) :
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()
        self.cur.execute("""
                            CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                email TEXT NOT NULL UNIQUE,
                                pass_hash TEXT NOT NULL,
                                register TEXT NOT NULL,
                                urls TEXT DEFAULT "[]" NOT NULL,
                                payment TEXT DEFAULT ""
                                )
                        """)
        self.con.commit()

        self.x_ui = py3xui.Api(host, username, passwd)
        self.x_ui.login()
        self.inbaund_id = inbaund_id
        self.inbaund_url = inbaund_url
        self.inbaund_port = inbaund_port

    def read_table(self, sql_command: str, params=None) -> dict :
        if params == None :
            params = ()
        return json.loads(pandas.read_sql(sql_command, self.con, params=params).to_json())
    
    def get_hash(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()
    
    def registration(self, email: str, passwd: str) -> dict :
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
        return {"code": 0, "data": {"id": int(data["id"]["0"]), "email": email}}
        
    def login(self, email: str, passwd: str) -> dict :
        """
        0 - Success
        1 - Incorrect email or password
        """
        data = self.read_table("""
                                    SELECT id, urls FROM users
                                    WHERE email = ? AND pass_hash = ?
                                """, (email, self.get_hash(passwd)))
        if data["id"] == {} :
            return {"code": 1}
        return {"code": 0, "data": {"id": int(data["id"]["0"]), "email": email, "urls": json.loads(data["urls"]["0"])}}
        
    def add_url(self, email: str, passwd: str, url_name: str) -> dict :
        """
        0 - Success
        1 - Incorrect email or password
        2 - The url already exists
        """
        data = self.read_table("""
                                    SELECT id, urls FROM users
                                    WHERE email = ? AND pass_hash = ?
                                """, (email, self.get_hash(passwd)))
        if data["id"] == {} :
            return {"code": 1}
        urls = json.loads(data["urls"]["0"])
        if url_name in urls :
            return {"code": 2}

        uid = str(uuid.uuid4())
        new_client = py3xui.Client(id=uid, email=f"{email}-{url_name}", enable=True, flow="xtls-rprx-vision")
        self.x_ui.client.add(self.inbaund_id, new_client)
        
        inbound = py3xui.Inbound(id=self.inbaund_id)
        pbk = inbound.stream_settings.reality_settings.get("settings").get("publicKey")
        wn = inbound.stream_settings.reality_settings.get("serverNames")[0]
        short_id = inbound.stream_settings.reality_settings.get("shortIds")[0]
        url = f"vless://{uid}@{self.inbaund_url}:{self.inbaund_port}?security=reality&pbk={pbk}&fp=random&sni={wn}&sid={short_id}&spx=%2F&flow=xtls-rprx-vision#SpectralVPN-{url_name}"
        
        urls.append(url_name)

        self.cur.execute("""
                                UPDATE users SET
                                urls = ?
                                WHERE id = ?
                        """, (json.dumps(urls), int(data["id"]["0"])))
        data = self.read_table("""
                                    SELECT id, urls FROM users
                                    WHERE email = ? AND pass_hash = ?
                                """, (email, self.get_hash(passwd)))
        
        return {"code": 0, "data": {"id": int(data["id"]["0"]), "email": email, "urls": json.loads(data["urls"]["0"]), "url": url}}
    
    def get_url(self, email: str, passwd: str, url_name: str) -> dict :
        """
        0 - Success
        1 - Incorrect email or password
        2 - The url does not exist
        """
        data = self.read_table("""
                                    SELECT id, urls FROM users
                                    WHERE email = ? AND pass_hash = ?
                                """, (email, self.get_hash(passwd)))
        if data["id"] == {} :
            return {"code": 1}
        urls = json.loads(data["urls"]["0"])
        if not url_name in urls :
            return {"code": 2}
        
        uid = self.x_ui.client.get_by_email(f"{email}-{url_name}").uuid
        inbound = py3xui.Inbound(id=self.inbaund_id)
        pbk = inbound.stream_settings.reality_settings.get("settings").get("publicKey")
        wn = inbound.stream_settings.reality_settings.get("serverNames")[0]
        short_id = inbound.stream_settings.reality_settings.get("shortIds")[0]
        url = f"vless://{uid}@{self.inbaund_url}:{self.inbaund_port}?security=reality&pbk={pbk}&fp=random&sni={wn}&sid={short_id}&spx=%2F&flow=xtls-rprx-vision#SpectralVPN-{url_name}"
        
        return {"code": 0, "data": {"id": int(data["id"]["0"]), "email": email, "urls": urls, "url": url}}

    def del_url(self, email: str, passwd: str, url_name: str) -> dict :
        """
        0 - Success
        1 - Incorrect email or password
        2 - The url does not exist
        """
        data = self.read_table("""
                                    SELECT id, urls FROM users
                                    WHERE email = ? AND pass_hash = ?
                                """, (email, self.get_hash(passwd)))
        if data["id"] == {} :
            return {"code": 1}
        urls = json.loads(data["urls"]["0"])
        if not url_name in urls :
            return {"code": 2}
        
        uid = self.x_ui.client.get_by_email(f"{email}-{url_name}").uuid
        self.x_ui.client.delete(self.inbaund_id, uid)
        urls.remove(url_name)
        self.cur.execute("""
                                UPDATE users SET
                                urls = ?
                                WHERE id = ?
                        """, (json.dumps(urls), int(data["id"]["0"])))
        data = self.read_table("""
                                    SELECT id, urls FROM users
                                    WHERE email = ? AND pass_hash = ?
                                """, (email, self.get_hash(passwd)))
        return {"code": 0, "data": {"id": int(data["id"]["0"]), "email": email, "urls": urls}}
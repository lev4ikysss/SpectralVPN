import sqlite3
import pandas
import datetime
import hashlib
import json
import uuid
import requests
import random

class API :
    def __init__(self, path: str, host: str, username: str, passwd: str, inbaund_id: int, inbaund_url: str) :
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

        self.x_ui = requests.Session()
        self.x_ui.verify = True
        self.x_ui.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; py3xui-like)"
        })
        response = self.x_ui.post(f"{host}/login", json={
            "username": username,
            "password": passwd
        })
        response.raise_for_status()
        self.host = host

        self.inbaund_id = inbaund_id
        self.inbaund_url = inbaund_url

    def read_table(self, sql_command: str, params=None) -> dict :
        if params == None :
            params = ()
        return json.loads(pandas.read_sql(sql_command, self.con, params=params).to_json())
    
    @staticmethod
    def get_hash(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()
    
    def response(self, method: str, endpoint: str, **kwargs) :
        response = self.x_ui.request(method, f"{self.host}/panel/{endpoint}", **kwargs)
        response.raise_for_status()
        return response.json()

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
                               """, (email,))
        return {"code": 0, "data": {"id": int(data["id"]["0"]), "email": email}}
        
    def close(self) :
        self.con.close()

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
        
        response = self.response("post", "inbound/list")
        inbaund = None
        for i in response["obj"] :
            if i["id"] == self.inbaund_id :
                inbaund = i
                break
        if inbaund == None :
            raise TypeError
        stream = json.loads(inbaund["streamSettings"])
        suid = random.choice(stream["realitySettings"]["shortIds"])
        sni = random.choice(stream["realitySettings"]["serverNames"])
        pbk = stream["realitySettings"]["settings"]["publicKey"]
        uid = str(uuid.uuid4())

        response = self.response("post", "inbound/addClient", json={
            "id": self.inbaund_id,
            "settings": json.dumps({
                "clients":[{
                    "id": uid,
                    "flow": "xtls-rprx-vision",
                    "email": f"{email}-{url_name}",
                    "limitIp": 0,
                    "totalGB": 0,
                    "expiryTime": 0,
                    "enable": True,
                    "tgId": "",
                    "subId": suid,
                    "comment": "",
                    "reset": 0
                }]
            })
        })
        
        response = self.response("post", "inbound/list")
        inbaund = None
        for i in response["obj"] :
            if i["id"] == self.inbaund_id :
                inbaund = i
                break
        if inbaund == None :
            raise TypeError
        
        url = f"vless://{uid}@{self.inbaund_url}?security=reality&pbk={pbk}&fp=random&sni={sni}&sid={suid}&spx=%2F&flow=xtls-rprx-vision#SpectralVPN-{url_name}"
        
        urls.append(url_name)

        self.cur.execute("""
                                UPDATE users SET
                                urls = ?
                                WHERE id = ?
                        """, (json.dumps(urls), int(data["id"]["0"])))
        self.con.commit()
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
        
        response = self.response("post", "inbound/list")
        inbaund = None
        for i in response["obj"] :
            if i["id"] == self.inbaund_id :
                inbaund = i
                break
        if inbaund == None :
            raise TypeError
        stream = json.loads(inbaund["streamSettings"])
        suid = random.choice(stream["realitySettings"]["shortIds"])
        sni = random.choice(stream["realitySettings"]["serverNames"])
        pbk = stream["realitySettings"]["settings"]["publicKey"]
        client = None
        for i in json.loads(inbaund["settings"])["clients"] :
            if i["email"] == f"{email}-{url_name}" :
                client = i
                break
        if client == None :
            raise TypeError
        uid = client["id"]
        url = f"vless://{uid}@{self.inbaund_url}?security=reality&pbk={pbk}&fp=random&sni={sni}&sid={suid}&spx=%2F&flow=xtls-rprx-vision#SpectralVPN-{url_name}"
        
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
        
        response = self.response("post", "inbound/list")
        inbaund = None
        for i in response["obj"] :
            if i["id"] == self.inbaund_id :
                inbaund = i
                break
        if inbaund == None :
            raise TypeError
        client = None
        for i in json.loads(inbaund["settings"])["clients"] :
            if i["email"] == f"{email}-{url_name}" :
                client = i
                break
        if client == None :
            raise TypeError
        uid = client["id"]
        self.response("post", f"inbound/{self.inbaund_id}/delClient/{uid}")

        urls.remove(url_name)
        self.cur.execute("""
                                UPDATE users SET
                                urls = ?
                                WHERE id = ?
                        """, (json.dumps(urls), int(data["id"]["0"])))
        self.con.commit()
        data = self.read_table("""
                                    SELECT id, urls FROM users
                                    WHERE email = ? AND pass_hash = ?
                                """, (email, self.get_hash(passwd)))
        return {"code": 0, "data": {"id": int(data["id"]["0"]), "email": email, "urls": urls}}
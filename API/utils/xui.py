import json
import uuid
import random
from urllib.parse import quote
from httpx import AsyncClient
from fastapi import HTTPException

class Configs:
    def __init__(self, inbound_id: int, host: str, client_email: str, display_name: str):
        self.inbound_id = inbound_id
        self.host = host
        self.client_email = client_email
        self.display_name = display_name

    async def legacy_payload(self, data: dict,) -> dict:
        inbounds = data.get("obj")
        inbound = next((i for i in inbounds if i.get("id") == self.inbound_id), None)
        if not inbound:
            raise HTTPException(
                status_code=404,
                detail=f"Server not found"
            )
        stream_settings = json.loads(inbound.get("streamSettings"))
        reality = stream_settings.get("realitySettings")
        short_ids = reality.get("shortIds")
        suid = random.choice(short_ids)
        client_uuid = str(uuid.uuid4())
        return {
            "id": self.inbound_id,
            "settings": json.dumps({
                "clients": [{
                    "id": client_uuid,
                    "flow": "xtls-rprx-vision",
                    "email": self.client_email,
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
        }

    async def legacy_config(self, data: dict) -> str:
        inbounds = data.get("obj")
        inbound = next((i for i in inbounds if i.get("id") == self.inbound_id), None)
        if not inbound:
            raise HTTPException(
                status_code=500,
                detail="Server error"
            )
        settings = json.loads(inbound.get("settings"))
        clients = settings.get("clients")
        current_client = next((i for i in clients if i.get("email") == self.client_email), None)
        if not current_client:
            raise HTTPException(
                status_code=500,
                detail="Server error"
            )
        client_uuid = current_client.get("id")
        sub_id = current_client.get("subId")
        stream_settings = json.loads(inbound.get("streamSettings"))
        reality = stream_settings.get("realitySettings")
        server_names = reality.get("serverNames")
        setting = reality.get("settings")
        pbk = setting.get("publicKey")
        fp = setting.get("fingerprint")
        spx = quote(setting.get("spiderX"), safe='')
        sni = random.choice(server_names)
        port = inbound.get("port")
        return (
            f"vless://{client_uuid}@{self.host}:{port}?"
            f"security=reality&"
            f"pbk={pbk}&"
            f"fp={fp}&"
            f"sni={sni}&"
            f"sid={sub_id}&"
            f"spx={spx}&"
            f"flow=xtls-rprx-vision#"
            f"{self.display_name}"
        )

class XUIClient:
    def __init__(self, host: str, base_url: str, username: str, password: str, inbound_id: int, version: str):
        self.host = host
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.inbound_id = inbound_id
        self.session = AsyncClient(timeout=20.0)
        self.logged_in = False
        self.version = version

    @classmethod
    async def from_server(cls, server):
        #TODO заменить на https
        base_url = f"http://{server.host}:{server.port}"
        return cls(server.host, base_url, server.user, server.password, server.inbound_id, server.version)

    async def _login(self):
        if self.logged_in:
            return
        try:
            resp = await self.session.post(
                f"{self.base_url}/login",
                json={"username": self.username, "password": self.password}
            )
            resp.raise_for_status()
            self.logged_in = True
        except:
            raise HTTPException(
                status_code=500,
                detail="Server error"
            )

    async def add_client(self, client_email: str, display_name: str) -> str:
        configs = Configs(self.inbound_id, self.host, client_email, display_name)
        await self._login()
        resp = await self.session.post(f"{self.base_url}/panel/inbound/list")
        resp.raise_for_status()
        if self.version == "legacy":
            resp = await self.session.post(f"{self.base_url}/panel/inbound/addClient", json=configs.legacy_payload(resp.json()))
        else:
            raise HTTPException(
                status_code=500,
                detail="Server error"
            )
        resp.raise_for_status()
        resp = await self.session.post(f"{self.base_url}/panel/inbound/list")
        resp.raise_for_status()
        if self.version == "legacy":
            return configs.legacy_config(resp.json())
        else:
            raise HTTPException(
                status_code=500,
                detail="Server error"
            )

    async def get_client_traffic(self, client_email: str) -> int:
        await self._login()
        try:
            resp = await self.session.post(f"{self.base_url}/panel/inbound/list")
            resp.raise_for_status()
            data = resp.json()
            inbounds = data.get("obj")
            for inbound in inbounds:
                client_stats = inbound.get("clientStats")
                for stat in client_stats:
                    if stat.get("email") == client_email:
                        up = stat.get("up")
                        down = stat.get("down")
                        return up + down
            return 0
        except:
            return 0

    async def delete_client(self, client_email: str):
        await self._login()
        try:
            resp = await self.session.post(
                f"{self.base_url}/panel/inbound/{self.inbound_id}/delClientByEmail/{client_email}"
            )
            resp.raise_for_status()
            return
        except:
            HTTPException(
                status_code=500,
                detail="Server error"
            )

    async def close(self):
        await self.session.aclose()

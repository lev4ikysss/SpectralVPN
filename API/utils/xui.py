import json
import uuid
import random
from httpx import AsyncClient
from fastapi import HTTPException

class XUIClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.session = AsyncClient(timeout=20.0)
        self.logged_in = False

    @classmethod
    async def from_server(cls, server):
        #TODO заменить на https
        base_url = f"http://{server.host}:{server.port}"
        return cls(base_url, server.user, server.password)

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

    async def add_client(self, inbound_id: int, client_email: str, display_name: str) -> str:
        await self._login()
        resp = await self.session.post(f"{self.base_url}/panel/inbound/list")
        resp.raise_for_status()
        data = resp.json()
        inbounds = data.get("obj", [])
        inbound = next((i for i in inbounds if i.get("id") == inbound_id), None)
        if not inbound:
            raise HTTPException(
                status_code=404,
                detail=f"Server not found"
            )
        stream_settings = json.loads(inbound.get("streamSettings", "{}"))
        reality = stream_settings.get("realitySettings", {})
        short_ids = reality.get("shortIds", [""])
        server_names = reality.get("serverNames", {})
        suid = random.choice(short_ids)
        sni = random.choice(server_names)
        pbk = reality.get("settings", {}).get("publicKey", "")
        client_uuid = str(uuid.uuid4())
        add_payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [{
                    "id": client_uuid,
                    "flow": "xtls-rprx-vision",
                    "email": client_email,
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
        resp = await self.session.post(f"{self.base_url}/panel/inbound/addClient", json=add_payload)
        resp.raise_for_status()
        host = inbound.get("remark")
        config_url = (
            f"vless://{client_uuid}@{host}?"
            f"security=reality&"
            f"pbk={pbk}&"
            f"fp=random&"
            f"sni={sni}&"
            f"sid={suid}&"
            f"spx=%2F&"
            f"flow=xtls-rprx-vision#"
            f"{display_name}"
        )
        return config_url

    async def get_client_traffic(self, client_email: str) -> int:
        await self._login()
        try:
            resp = await self.session.post(
                f"{self.base_url}/panel/inbound/getClientTraffics/{client_email}"
            )
            resp.raise_for_status()
            data = resp.json()
            obj = data.get("obj", {})
            return obj.get("down", 0) + obj.get("up", 0)
        except:
            return 0

    async def delete_client(self, inbound_id: int, client_email: str):
        await self._login()
        try:
            resp = await self.session.post(
                f"{self.base_url}/panel/inbound/{inbound_id}/delClientByEmail/{client_email}"
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

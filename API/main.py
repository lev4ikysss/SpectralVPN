from fastapi import FastAPI, HTTPException, Request
import subprocess
import json
import hashlib
import datetime
import random

def bash_command(bash_command) :
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    return output

tarifs = {
    "None": 0,
    "Стандартный": 2,
    "Семейный": 7,
    "Корпаративный": 100
}

app = FastAPI()

class User_reg() :
    name: str
    email: str
    passwd: str
    invite_code: str
    privacy_claimed: bool

@app.post("/user.add")
def registration(user: User_reg, request: Request) :
    if not user.privacy_claimed :
        raise HTTPException(400, "Dont accept terms")
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    else:
        client_ip = request.client.host
    if not client_ip:
        raise HTTPException(400, "IP address not detected")
    time = datetime.datetime
    with open('main_data.json', 'r') as file :
        Data = json.load(file)
    invite = -1
    id = len(Data["users"])
    for i in Data["users"] :
        if i["email"] == user.email :
            raise HTTPException(400, "The email already exists")
        if user.invite_code == i["invite_code"] :
            invite = i["id"]
    if user.invite_code != "" :
        if invite == -1 :
            raise HTTPException(400, "The invite code is invalid")
        else :
            pass
            # Тут чёта для поощерения вставить, лол invite: id человека пригласившего
    Data["users"].append({
        "id": id,
        "name": user.name,
        "email": user.email,
        "passwd_hash": hashlib.sha256(user.passwd.encode()),
        "ip_reg": client_ip,
        "vers_of_terms": "v1",
        "invite_code": hashlib.sha256(str(id).encode())[:8],
        "token_user": hashlib.sha256(str(random.random()).encode()),
        "users_score": 0,
        "tarif": "None",
        "time_payment": {
            "year": 0,
            "month": 0,
            "day": 0,
            "hour": 0,
            "minute": 0,
            "second": 0
        },
        "time_reg": {
            "year": time.year,
            "month": time.month,
            "day": time.day,
            "hour": time.hour,
            "minute": time.minute,
            "second": time.second
        }
    })
    with open('main_data.json', 'w') as file :
        json.dump(Data, file, indent=4)
    return {
        "id": Data["users"][id]["id"],
        "name": Data["users"][id]["name"],
        "email": Data["users"][id]["email"],
        "token-user": Data["users"][id]["token_user"],
        "tarif": Data["users"][id]["tarif"],
        "users-score": Data["users"][id]["users_score"]
    }

class User_get() :
    email: str
    passwd: str

@app.get("/user.login")
def login(user: User_get) :
    id = -1
    with open('main_data.json', 'r') as file :
        Data = json.load(file)
    for i in Data["users"] :
        if i["email"] == user.email :
            id = i["id"]
            break
    if id == -1 :
        raise HTTPException(400, "Incorrect email")
    if Data["users"][id]["passwd_hash"] != hashlib.sha256(user.passwd.encode()) :
        raise HTTPException(400, "Incorrect password")
    return {
        "id": Data["users"][id]["id"],
        "name": Data["users"][id]["name"],
        "email": Data["users"][id]["email"],
        "token_user": Data["users"][id]["token_user"],
        "tarif": Data["users"][id]["tarif"],
        "users_score": Data["users"][id]["users_score"]
    }

#пополнение/покупка тарифа

class wg_form() :
    id: int
    product: str
    token_user: str

@app.get("/wireguard.make")
def wg_mk(parameters: wg_form) :
    if not parameters.product in ["Wireguard", "ShadowSocks", "VLESS"] :
        raise HTTPException(400, "No product")
    with open('main_data.json', 'r') as file :
        Data = json.load(file)
    if len(Data["users"]) <= parameters.id :
        raise HTTPException(400, "Unknown user")
    if Data["users"][parameters.id]["users_score"] <= 0 :
        raise HTTPException(401, "The product has not been purchased")
    if Data["users"][parameters.id]["token_user"] == parameters.token_user :
        raise HTTPException(400, "Incorrect token")
    Data["users"][parameters.id]["users_score"] -= 1
    with open('main_data.json', 'w') as file :
        json.dump(Data, file, indent=4)
    num = tarifs[Data["users"][parameters.id]["tarif"]] - Data["users"][parameters.id]["users_score"] + 1
    answer = ""
    url = ""
    if parameters.product == "Wireguard" :
        answer = bash_command(f"./create_wg.sh {parameters.token_user} {Data["users"][parameters.id]["name"]} {num}")
    elif parameters.product == "ShadowSocks" :
        answer = bash_command(f"./create_ss.sh {parameters.token_user} {Data["users"][parameters.id]["name"]} {num}")
    elif parameters.product == "VLESS" :
        url = bash_command(f"./create_vl.py {parameters.token_user} {Data["users"][parameters.id]["name"]} {num}")
    return {
        "roads": answer.split(","),
        "url": url,
        "protocol": parameters.product
    }

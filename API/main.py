from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
import configparser
import utils

app = FastAPI()

config = configparser.ConfigParser()
config.read('params.conf', encoding='utf-8')
args = [
    config["api"]["path"],
    config["api"]["host"],
    config["api"]["username"],
    config["api"]["password"],
    config.getint("api", "inbaund_id"),
    config["api"]["inbaund_url"]
    ]

class RegisterBody(BaseModel) :
    email : EmailStr
    password : str

class LoginBody(BaseModel) :
    email : EmailStr
    password : str

class UrlsBody(BaseModel) :
    urls_name : str
    email : EmailStr
    password : str

@app.post("/registration", status_code=status.HTTP_201_CREATED)
def registration(body: RegisterBody) :
    methods = utils.API(*args)
    result = methods.registration(body.email, body.password)
    methods.close()
    if result["code"] == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is busy."
        )
    return result["data"]
    
@app.post("/login", status_code=status.HTTP_200_OK)
def login(body: LoginBody) :
    methods = utils.API(*args)
    answer = methods.login(body.email, body.password)
    methods.close()
    if answer["code"] == 1 :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )
    else :
        return answer["data"]

@app.post("/add_url", status_code=status.HTTP_200_OK)
def add_url(body: UrlsBody) :
    methods = utils.API(*args)
    answer = methods.add_url(body.email, body.password, body.urls_name)
    methods.close()
    if answer["code"] == 1 :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )
    elif answer["code"] == 2 :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The url already exists."
        )
    else :
        return answer["data"]

@app.get("/get_url", status_code=status.HTTP_200_OK)
def get_url(email: EmailStr = Query(...), password: str = Query(...), urls_name: str = Query(...)) :
    methods = utils.API(*args)
    answer = methods.get_url(email, password, urls_name)
    methods.close()
    if answer["code"] == 1 :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )
    elif answer["code"] == 2 :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The url does not exist"
        )
    else :
        return answer["data"]

@app.delete("/del_url", status_code=status.HTTP_200_OK)
def del_url(email: EmailStr = Query(...), password: str = Query(...), urls_name: str = Query(...)) :
    methods = utils.API(*args)
    answer = methods.del_url(email, password, urls_name)
    methods.close()
    if answer["code"] == 1 :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )
    elif answer["code"] == 2 :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The url does not exist"
        )
    else :
        return answer["data"]

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
import utils

app = FastAPI()
db = utils.DataBase("")

class RegisterBody(BaseModel) :
    email : EmailStr
    password : str

class LoginBody(BaseModel) :
    email : EmailStr
    password : str


@app.post("/registration", status_code=status.HTTP_201_CREATED)
def registration(body: RegisterBody) :
    result = db.registration(body.email, body.password)
    if result["code"] == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is busy."
        )
    return result["data"]
    
@app.post("/login", status_code=status.HTTP_200_OK)
def login(body: LoginBody) :
    answer = db.login(body.email, body.password)
    if answer["code"] == 1 :
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password."
        )
    else :
        return answer["data"]
from fastapi import FastAPI, HTTPException
import utils

app = FastAPI()
db = utils.DataBase("")

@app.post("/registration")
def reg(email: str, password: str) :
    answer = db.registration(email, password)
    if answer["code"] == 1 :
        HTTPException(400, "Email is busy.")
    else :
        return answer["data"]
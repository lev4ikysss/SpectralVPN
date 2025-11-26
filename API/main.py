import configparser
import fastapi
from fastapi import HTTPException
import utils

config = configparser.ConfigParser()
config.read('../configs/settings.conf', encoding='utf-8')
path = config['database']['path']

DB = utils.DataBase(path=path)

app = fastapi.FastAPI()

@app.post("/web/registration/")
def reg(email: str, passwd: str) :
    code = DB.register_site(email, passwd)
    if code == 0 :
        return 200
    else :
        raise HTTPException(
            status_code=400,
            detail="Этот email уже зарегистрирован"
        )

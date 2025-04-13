from fastapi import FastAPI
import subprocess

def bash_command(bash_command) :
    """
    Выполняет Bash команду и возвращает ответ

    :param bash_command: Команда bash
    :return: Ответ команды
    """
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    return output

app = FastAPI()

@app.get("/get.wg")
def get_wg_cfg() :
    a = bash_command("bash /home/palchik/Programms/Python/Project_api/test.sh")
    return {"message": a}
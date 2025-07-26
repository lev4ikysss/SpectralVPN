#!/usr/bin/python3
#./create_vl.py {token} {name} {num}
from vless_api_lib import X3API as X3
import click

api = X3("#", "#", "#")

@click.command()
@click.argument("token", type=str)
@click.argument("name", type=str)
@click.argument("number", type=str)
def main(token, name, number) :
    status = api.add_client(0, 0, f"{name}-{number}")
    if status["success"] != True :
        api.update_client(0, f"{name}-{number}", True)
    url = api.get_connection_link(f"{name}-{number}")
    print(url, end="")

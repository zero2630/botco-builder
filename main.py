import subprocess
import json
from typing import List

from fastapi import FastAPI
import uvicorn
import requests

import builder

app = FastAPI()

processes = {}


def load_data():
    global processes

    with open("data.json", "r") as f:
        processes = json.load(f)

def check_token(token):
    data = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()

    if data["ok"]:
        return True

    return False

def return_answer(status: str=None, messages: List[str]=None, errors: List[str]=None):
    status = status or ""
    messages =  messages or []
    errors = errors or []

    answer = {
        "status": status,
        "messages": messages,
        "erorrs": errors,
    }

    return answer


@app.get("/bot/{bot_id}/")
def info(bot_id: int):
    bot_id = str(bot_id)

    return {"status": processes[bot_id]["status"], }


@app.post("/bot/{bot_id}/activate/")
def activate(bot_id: int):
    bot_id = str(bot_id)

    if bot_id in processes:
        if processes[bot_id]["status"] == "stopped":
            processes[bot_id] = {
                    "process": subprocess.Popen(["python", f"bots/{bot_id}/bot.py"]),
                    "status": "running",
                }

            return return_answer(
                status="bot activated",
                messages=["bot activated"],
            )

        return return_answer(
            status="bot activated",
            messages=["bot already activated"],
        )

    return return_answer(
        errors=["bot with this id doesn't exist"],
    )


@app.post("/bot/{bot_id}/deactivate/")
def deactivate(bot_id: int):
    bot_id = str(bot_id)

    if bot_id in processes:
        if processes[bot_id]["status"] == "running":
            processes[bot_id]["process"].terminate()
            processes[bot_id]["status"] = "stopped"

            return return_answer(
                status="bot deactivated",
                messages=["bot deactivated"],
            )

        return return_answer(
            status="bot deactivated",
            messages=["bot already deactivated"],
        )

    return return_answer(
        errors=["bot with this id doesn't exist"],
    )


@app.post("/bot/{bot_id}/set_token/")
def deactivate(bot_id: int, token: str):
    bot_id = str(bot_id)

    if bot_id in processes:
        if not check_token(token):
            return return_answer(
                errors=["your token isn't valid"]
            )

        if processes[bot_id]["status"] == "running":
            processes[bot_id]["process"].terminate()
            processes[bot_id]["status"] = "stopped"

        with open(f"bots/{bot_id}/conf.json", "w") as f:
            json.dump(
                {"token": token},
                f
            )

        return return_answer(
            status="bot deactivated",
            messages=["token was changed"],
        )

    return return_answer(
        errors=["bot with this id doesn't exist"],
    )


@app.post("/bot/create/")
def create(bot_id: int):
    bot_id = str(bot_id)

    if bot_id not in processes:
        builder.build_default(bot_id)
        builder.add_bot_to_data(bot_id)

        processes[bot_id] = {}
        processes[bot_id]["process"] = None
        processes[bot_id]["status"] = "stopped"

        return return_answer(
            status="bot deactivated",
            messages=["new bot was created"],
        )

    return return_answer(
        errors=["bot with this id doesn't exist"],
    )


if __name__ == "__main__":
    load_data()
    uvicorn.run(app, host="127.0.0.1", port=8001)

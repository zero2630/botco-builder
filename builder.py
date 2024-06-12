from jinja2 import Environment, FileSystemLoader

import os
import json

file_loader =  FileSystemLoader("templates")
env = Environment(loader=file_loader)


def build_default(bot_id):
    os.mkdir(f"bots/{bot_id}")
    with open(f"bots/{bot_id}/bot.py", "w") as f:
        template = env.get_template("default_template")
        f.write(template.render(bot_id=bot_id))
    with open(f"bots/{bot_id}/conf.json", "w") as f:
        json.dump(
            {"token": None},
            f)


def add_bot_to_data(bot_id):
    with open("data.json", "r") as f:
        data = json.load(f)

    data[bot_id] = {}
    data[bot_id]["process"] = None
    data[bot_id]["status"] = "stopped"

    with open("data.json", "w") as f:
        json.dump(data, f)

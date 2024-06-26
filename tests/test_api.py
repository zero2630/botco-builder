import json
import pathlib

from parameterized import parameterized

import src.config
from tests.conftest import client

__all__ = [
    "test_activate_bot",
    "test_allbots",
    "test_archive_bot",
    "test_build_bot",
    "test_create_bot",
    "test_deactivate_bot",
    "test_delete_bot",
    "test_get_bot",
    "test_load_media_bot",
    "test_set_token_bot",
    "test_user",
]


SECRET_KEY = src.config.SECRET_KEY

with pathlib.Path("./json_new_example.json").open("r") as f:
    success_blueprint = json.load(f)

failure_blueprint1 = {}
failure_blueprint2 = {"keyboards": [], "blocks": []}


@parameterized.expand(
    [
        [
            "fake",
            "test_user_token",
            "no roots",
            "errors",
        ],
        [
            SECRET_KEY,
            "test_user_token",
            "ok",
            "messages",
        ],
        [
            SECRET_KEY,
            "test_user_token2",
            "ok",
            "messages",
        ],
    ],
)
def test_user(key, user_token, answ, answ_type):
    response = client.post(
        f"/api/user/create/?user_token={user_token}&secret_key={key}",
    )
    assert response.status_code == 200
    assert answ in response.json()[answ_type]


@parameterized.expand(
    [
        [
            "test_user_token",
            "test_bot",
            "ok",
            "messages",
        ],
        [
            "fake_user_token",
            "test_bot2",
            "user with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot2",
            "ok",
            "messages",
        ],
        [
            "test_user_token",
            "test_bot",
            "bot with this uid already exist",
            "errors",
        ],
    ],
)
def test_create_bot(user_token, bot_uid, answ, answ_type):
    response = client.post(
        f"/api/bot/create/?user_token={user_token}&bot_uid={bot_uid}",
    )
    assert response.status_code == 200
    assert answ in response.json()[answ_type]
    if answ == "ok":
        assert bot_uid in [i.name for i in pathlib.Path("./bots").glob("*")]


@parameterized.expand(
    [
        [
            "test_user_token2",
            "test_bot",
            "no roots",
            "errors",
        ],
        [
            "fake_user_token",
            "test_bot",
            "user with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot3",
            "bot with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot",
            "test_bot",
            "uid",
        ],
        [
            "test_user_token",
            "test_bot2",
            "test_bot2",
            "uid",
        ],
    ],
)
def test_get_bot(user_token, bot_uid, answ, answ_type):
    response = client.get(f"/api/bot/{bot_uid}/?user_token={user_token}")
    assert response.status_code == 200
    assert answ in response.json()[answ_type]


@parameterized.expand(
    [
        ["test_user_token2", [], None],
        ["fake_user_token", "user with this token doesn't exist", "errors"],
        ["test_user_token", ["test_bot", "test_bot2"], None],
    ],
)
def test_allbots(user_token, answ, answ_type):
    response = client.get(f"/api/user/allbots/?user_token={user_token}")
    assert response.status_code == 200
    if answ_type:
        assert answ in response.json()[answ_type]
    else:
        assert response.json() == answ


@parameterized.expand(
    [
        [
            "test_user_token2",
            "test_bot",
            src.config.BOT_TOKEN_TEST,
            "no roots",
            "errors",
        ],
        [
            "fake_user_token",
            "test_bot",
            src.config.BOT_TOKEN_TEST,
            "user with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot3",
            src.config.BOT_TOKEN_TEST,
            "bot with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot",
            "fake_token",
            "your token isn't valid",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot",
            src.config.BOT_TOKEN_TEST,
            "ok",
            "messages",
        ],
    ],
)
def test_set_token_bot(user_token, bot_uid, new_token, answ, answ_type):
    response = client.post(
        f"/api/bot/{bot_uid}/set_token/?"
        f"user_token={user_token}&"
        f"new_token={new_token}",
    )
    assert response.status_code == 200
    assert answ in response.json()[answ_type]
    if answ == "ok":
        with pathlib.Path(f"./bots/{bot_uid}/conf.json").open("r") as f:
            a = json.load(f)
            assert a["token"] == new_token


@parameterized.expand(
    [
        [
            "test_user_token2",
            "test_bot",
            success_blueprint,
            "no roots",
            "errors",
            200,
        ],
        [
            "fake_user_token",
            "test_bot",
            success_blueprint,
            "user with this token doesn't exist",
            "errors",
            200,
        ],
        [
            "test_user_token",
            "test_bot3",
            success_blueprint,
            "bot with this token doesn't exist",
            "errors",
            200,
        ],
        [
            "test_user_token",
            "test_bot",
            failure_blueprint2,
            "no blocks",
            "errors",
            200,
        ],
        ["test_user_token", "test_bot", failure_blueprint1, None, None, 422],
        [
            "test_user_token",
            "test_bot",
            success_blueprint,
            "ok",
            "messages",
            200,
        ],
    ],
)
def test_build_bot(
    user_token,
    bot_uid,
    blueprint,
    answ,
    answ_type,
    status_code,
):
    response = client.post(
        f"/api/bot/{bot_uid}/build/?user_token={user_token}",
        json=blueprint,
    )
    assert response.status_code == status_code
    if status_code == 200:
        assert answ in response.json()[answ_type]


@parameterized.expand(
    [
        [
            "test_user_token2",
            "test_bot",
            "no roots",
            "errors",
        ],
        [
            "fake_user_token",
            "test_bot",
            "user with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot3",
            "bot with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot",
            "ok",
            "messages",
        ],
    ],
)
def test_load_media_bot(user_token, bot_uid, answ, answ_type):
    files = {
        "media_files": pathlib.Path("./json_new_example.json").open("rb"),
    }
    response = client.post(
        f"/api/bot/{bot_uid}/add_media?user_token={user_token}",
        files=files,
    )
    assert response.status_code == 200
    assert answ in response.json()[answ_type]
    if answ == "ok":
        assert "json_new_example.json" in [
            i.name for i in pathlib.Path("./bots/test_bot/media").glob("*")
        ]


@parameterized.expand(
    [
        [
            "test_user_token2",
            "test_bot",
            "no roots",
            "errors",
        ],
        [
            "fake_user_token",
            "test_bot",
            "user with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot3",
            "bot with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot",
            "bot activated",
            "messages",
        ],
        [
            "test_user_token",
            "test_bot",
            "bot already activated",
            "messages",
        ],
    ],
)
def test_activate_bot(user_token, bot_uid, answ, answ_type):
    response = client.post(
        f"/api/bot/{bot_uid}/activate/?user_token={user_token}",
    )
    assert response.status_code == 200
    assert answ in response.json()[answ_type]


@parameterized.expand(
    [
        [
            "test_user_token2",
            "test_bot",
            "no roots",
            "errors",
        ],
        [
            "fake_user_token",
            "test_bot",
            "user with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot3",
            "bot with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot",
            "bot deactivated",
            "messages",
        ],
        [
            "test_user_token",
            "test_bot",
            "bot already deactivated",
            "messages",
        ],
    ],
)
def test_deactivate_bot(user_token, bot_uid, answ, answ_type):
    response = client.post(
        f"/api/bot/{bot_uid}/deactivate/?user_token={user_token}",
    )
    assert response.status_code == 200
    assert answ in response.json()[answ_type]


@parameterized.expand(
    [
        [
            "test_user_token2",
            "test_bot",
            "no roots",
            "errors",
        ],
        [
            "fake_user_token",
            "test_bot",
            "user with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot3",
            "bot with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot",
            None,
            None,
        ],
    ],
)
def test_archive_bot(user_token, bot_uid, answ, answ_type):
    response = client.get(
        f"/api/bot/{bot_uid}/archive/?user_token={user_token}",
    )
    assert response.status_code == 200
    if answ:
        assert answ in response.json()[answ_type]
    else:
        assert "bot.zip" in [
            i.name for i in pathlib.Path("./archives/test_bot").glob("*")
        ]
        assert (
            pathlib.Path("./archives/test_bot/bot.zip").open("rb").read()
            == response.content
        )


@parameterized.expand(
    [
        [
            "test_user_token2",
            "test_bot2",
            "no roots",
            "errors",
        ],
        [
            "fake_user_token",
            "test_bot",
            "user with this token doesn't exist",
            "errors",
        ],
        [
            "test_user_token",
            "test_bot2",
            "ok",
            "messages",
        ],
        [
            "test_user_token",
            "test_bot",
            "ok",
            "messages",
        ],
        [
            "test_user_token",
            "test_bot2",
            "bot with this token doesn't exist",
            "errors",
        ],
    ],
)
def test_delete_bot(user_token, bot_uid, answ, answ_type):
    response = client.post(
        f"/api/bot/{bot_uid}/delete/?user_token={user_token}",
    )
    assert response.status_code == 200
    assert answ in response.json()[answ_type]
    if answ == "ok":
        assert bot_uid not in [
            i.name for i in pathlib.Path("./bots").glob("*")
        ]

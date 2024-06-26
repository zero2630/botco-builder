from pydantic import BaseModel

__all__ = ["CreationBlueprint", "CreationBot"]


class Block(BaseModel):
    id: str | int
    type: str
    parameters: dict
    father: None | int | str
    children: list[int | str]


class Keyboard(BaseModel):
    name: str
    type: str
    rows: list[list[str]]


class CreationBlueprint(BaseModel):
    keyboards: list[Keyboard]
    blocks: list[Block]


class CreationBot(BaseModel):
    bot_uid: str
    user_token: str

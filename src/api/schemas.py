from typing import Dict, List

from pydantic import BaseModel

__all__ = ["CreationBlueprint", "CreationBot"]


class CreationBlueprint(BaseModel):
    keyboards: List[Dict]
    blocks: List[Dict]


class CreationBot(BaseModel):
    bot_uid: str
    user_token: str

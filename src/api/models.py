from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
)

metadata = MetaData()

bot = Table(
    "fastapi_bot",
    metadata,
    Column("id", Integer, primary_key=True),
    Column(
        "user_id",
        Integer,
        ForeignKey("fastapi_user.id", ondelete="CASCADE"),
    ),
    Column("uid", String),
    Column("blueprint", JSON, nullable=True),
    Column("last_start", DateTime, nullable=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column(
        "updated_at",
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    ),
)

user = Table(
    "fastapi_user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("token", String),
)

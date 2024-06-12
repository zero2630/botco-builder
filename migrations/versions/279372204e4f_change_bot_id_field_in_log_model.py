"""change bot_id field in log model

Revision ID: 279372204e4f
Revises: 256eb65d5d6e
Create Date: 2024-05-01 16:57:14.592767

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "279372204e4f"
down_revision: Union[str, None] = "256eb65d5d6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "fastapi_log_bot_id_fkey", "fastapi_log", type_="foreignkey"
    )
    op.create_foreign_key(
        None,
        "fastapi_log",
        "fastapi_bot",
        ["bot_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "fastapi_log", type_="foreignkey")
    op.create_foreign_key(
        "fastapi_log_bot_id_fkey",
        "fastapi_log",
        "fastapi_user",
        ["bot_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###
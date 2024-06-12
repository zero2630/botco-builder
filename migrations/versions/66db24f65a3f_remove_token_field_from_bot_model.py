"""remove token field from bot model

Revision ID: 66db24f65a3f
Revises: 279372204e4f
Create Date: 2024-05-03 18:57:14.344454

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "66db24f65a3f"
down_revision: Union[str, None] = "279372204e4f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("fastapi_bot", "token")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "fastapi_bot",
        sa.Column("token", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    # ### end Alembic commands ###
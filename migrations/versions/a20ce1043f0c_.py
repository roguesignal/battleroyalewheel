"""empty message

Revision ID: a20ce1043f0c
Revises: c7baf43fe773
Create Date: 2017-07-10 13:17:06.837768

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a20ce1043f0c'
down_revision = 'c7baf43fe773'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('spin', sa.Column('game_name', sa.String(), nullable=True))
    op.drop_column('spin', 'game')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('spin', sa.Column('game', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('spin', 'game_name')
    # ### end Alembic commands ###

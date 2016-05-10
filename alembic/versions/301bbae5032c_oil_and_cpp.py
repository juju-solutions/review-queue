"""oil and cpp

Revision ID: 301bbae5032c
Revises: 
Create Date: 2016-05-10 08:37:04.792307

"""

# revision identifiers, used by Alembic.
revision = '301bbae5032c'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('review', sa.Column('is_cpp', sa.Boolean(), nullable=True))
    op.add_column('review', sa.Column('is_oil', sa.Boolean(), nullable=True))
    op.add_column('review_history', sa.Column('is_cpp', sa.Boolean(), nullable=True))
    op.add_column('review_history', sa.Column('is_oil', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('review_history', 'is_oil')
    op.drop_column('review_history', 'is_cpp')
    op.drop_column('review', 'is_oil')
    op.drop_column('review', 'is_cpp')
    ### end Alembic commands ###

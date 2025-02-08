"""Initial migration

Revision ID: 1c54e6721bac
Revises: 
Create Date: 2025-02-08 22:36:10.325031

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1c54e6721bac'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('experiments',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('type', sa.Enum('AB_TEST', 'MULTIVARIATE', 'FEATURE_FLAG', name='experimenttype'), nullable=False),
    sa.Column('hypothesis', sa.String(), nullable=True),
    sa.Column('targeting_rules', sa.JSON(), nullable=True),
    sa.Column('parameters', sa.JSON(), nullable=True),
    sa.Column('status', sa.Enum('DRAFT', 'SCHEDULED', 'RUNNING', 'PAUSED', 'COMPLETED', 'STOPPED', name='experimentstatus'), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('ended_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('feature_definitions',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('data_type', sa.String(), nullable=False),
    sa.Column('possible_values', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('name')
    )
    op.create_table('metric_definitions',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('unit', sa.String(), nullable=True),
    sa.Column('data_type', sa.String(), nullable=False),
    sa.Column('aggregation_method', sa.String(), nullable=False),
    sa.Column('query_template', sa.String(), nullable=True),
    sa.Column('min_sample_size', sa.Integer(), nullable=True),
    sa.Column('min_effect_size', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('name')
    )
    op.create_table('experiment_metrics',
    sa.Column('experiment_id', sa.String(), nullable=False),
    sa.Column('metric_name', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
    sa.ForeignKeyConstraint(['metric_name'], ['metric_definitions.name'], ),
    sa.PrimaryKeyConstraint('experiment_id', 'metric_name')
    )
    op.create_table('guardrail_metrics',
    sa.Column('experiment_id', sa.String(), nullable=False),
    sa.Column('metric_name', sa.String(), nullable=False),
    sa.Column('threshold', sa.Float(), nullable=False),
    sa.Column('operator', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
    sa.ForeignKeyConstraint(['metric_name'], ['metric_definitions.name'], ),
    sa.PrimaryKeyConstraint('experiment_id', 'metric_name')
    )
    op.create_table('variants',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('experiment_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('config', sa.JSON(), nullable=True),
    sa.Column('traffic_percentage', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('assignments',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('experiment_id', sa.String(), nullable=False),
    sa.Column('variant_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('context', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ),
    sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('assignments')
    op.drop_table('variants')
    op.drop_table('guardrail_metrics')
    op.drop_table('experiment_metrics')
    op.drop_table('metric_definitions')
    op.drop_table('feature_definitions')
    op.drop_table('experiments')
    # ### end Alembic commands ###

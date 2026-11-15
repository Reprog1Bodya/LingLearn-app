"""add_indexes_and_notes

Revision ID: 7f8a9b0c1d2e
Revises: e47af060ab93
Create Date: 2026-11-04 23:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f8a9b0c1d2e'
down_revision: Union[str, Sequence[str], None] = 'e47af060ab93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Последующая миграция изменения схемы:
    1. Добавление колонки личных заметок к изучаемому слову (notes).
    2. Добавление составного индекса (user_id, is_learned) для ускорения фильтрации слов.
    3. Добавление индекса (user_id, created_at) для ускорения выборки истории тренировок.
    """
    with op.batch_alter_table('user_word_progress', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notes', sa.String(length=256), nullable=True))
        batch_op.create_index('ix_user_word_progress_user_learned', ['user_id', 'is_learned'], unique=False)

    with op.batch_alter_table('test_results', schema=None) as batch_op:
        batch_op.create_index('ix_test_results_user_created', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Откат последующей миграции."""
    with op.batch_alter_table('test_results', schema=None) as batch_op:
        batch_op.drop_index('ix_test_results_user_created')

    with op.batch_alter_table('user_word_progress', schema=None) as batch_op:
        batch_op.drop_index('ix_user_word_progress_user_learned')
        batch_op.drop_column('notes')

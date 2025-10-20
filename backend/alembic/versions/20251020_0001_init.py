from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '20251020_0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.create_table(
		'users',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('email', sa.String(length=255), nullable=False, unique=True),
		sa.Column('name', sa.String(length=100), nullable=False),
		sa.Column('role', sa.String(length=20), nullable=False, server_default='IR'),
		sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)
	op.create_index('ix_users_email', 'users', ['email'])

	op.create_table(
		'prompt_templates',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('name', sa.String(length=100), nullable=False, unique=True),
		sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
		sa.Column('content', sa.Text(), nullable=False),
		sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'import_batches',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('type', sa.String(length=50), nullable=False),
		sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
		sa.Column('file_path', sa.String(length=500), nullable=False),
		sa.Column('metadata', sa.JSON(), nullable=True),
		sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'knowledge_docs',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('title', sa.String(length=300), nullable=False),
		sa.Column('category', sa.String(length=50), nullable=False),
		sa.Column('source_path', sa.String(length=500), nullable=True),
		sa.Column('source_url', sa.String(length=500), nullable=True),
		sa.Column('disclosure_date', sa.Date(), nullable=True),
		sa.Column('batch_id', sa.Integer(), sa.ForeignKey('import_batches.id'), nullable=True),
		sa.Column('metadata', sa.JSON(), nullable=True),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'standard_answers',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('topic_key', sa.String(length=200), nullable=False, unique=True),
		sa.Column('description', sa.String(length=500), nullable=True),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'standard_answer_versions',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('standard_answer_id', sa.Integer(), sa.ForeignKey('standard_answers.id', ondelete='CASCADE'), nullable=False),
		sa.Column('version', sa.Integer(), nullable=False),
		sa.Column('content', sa.Text(), nullable=False),
		sa.Column('strong_constraint', sa.Boolean(), nullable=False, server_default=sa.text('0')),
		sa.Column('effective_from', sa.DateTime(), nullable=True),
		sa.Column('effective_to', sa.DateTime(), nullable=True),
		sa.Column('metadata', sa.JSON(), nullable=True),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'questions',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('asked_text', sa.Text(), nullable=False),
		sa.Column('normalized_text', sa.Text(), nullable=True),
		sa.Column('prompt_template_id', sa.Integer(), sa.ForeignKey('prompt_templates.id'), nullable=True),
		sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
		sa.Column('metadata', sa.JSON(), nullable=True),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'generated_answers',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('question_id', sa.Integer(), sa.ForeignKey('questions.id'), nullable=False),
		sa.Column('initial_answer', sa.Text(), nullable=False),
		sa.Column('aligned_answer', sa.Text(), nullable=True),
		sa.Column('alignment_summary', sa.Text(), nullable=True),
		sa.Column('sources_a', sa.JSON(), nullable=True),
		sa.Column('sources_b', sa.JSON(), nullable=True),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'review_tasks',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('question_id', sa.Integer(), sa.ForeignKey('questions.id'), nullable=False),
		sa.Column('generated_answer_id', sa.Integer(), sa.ForeignKey('generated_answers.id'), nullable=False),
		sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
		sa.Column('assignee_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
		sa.Column('comments', sa.Text(), nullable=True),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
		sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)

	op.create_table(
		'audit_logs',
		sa.Column('id', sa.Integer(), primary_key=True),
		sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
		sa.Column('action', sa.String(length=100), nullable=False),
		sa.Column('details', sa.JSON(), nullable=True),
		sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
	)


def downgrade() -> None:
	op.drop_table('audit_logs')
	op.drop_table('review_tasks')
	op.drop_table('generated_answers')
	op.drop_table('questions')
	op.drop_table('standard_answer_versions')
	op.drop_table('standard_answers')
	op.drop_table('knowledge_docs')
	op.drop_table('import_batches')
	op.drop_table('prompt_templates')
	op.drop_index('ix_users_email', table_name='users')
	op.drop_table('users')

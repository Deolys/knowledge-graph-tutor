"""tests/test_questions tables + LLM token columns on books

Revision ID: 002_tests_and_tokens
Revises: 001_initial
Create Date: 2026-06-13
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002_tests_and_tokens"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── Токены LLM на ingestion книги (оценка стоимости графа) ───
    op.add_column(
        "books",
        sa.Column("prompt_tokens", sa.Integer(), server_default=sa.text("0")),
    )
    op.add_column(
        "books",
        sa.Column(
            "completion_tokens", sa.Integer(), server_default=sa.text("0")
        ),
    )
    op.add_column(
        "books",
        sa.Column("total_tokens", sa.Integer(), server_default=sa.text("0")),
    )
    op.add_column(
        "books",
        sa.Column("llm_calls", sa.Integer(), server_default=sa.text("0")),
    )

    # ─── Тесты по графу ───
    op.create_table(
        "tests",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "book_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'ready'")),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime()),
    )
    op.create_index(
        "ix_tests_session_book", "tests", ["session_id", "book_id"]
    )

    op.create_table(
        "test_questions",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "test_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tests.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "entity_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entities.id", ondelete="SET NULL"),
        ),
        sa.Column("entity_name", sa.String()),
        sa.Column("order_num", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=False),
        sa.Column("correct_idx", sa.Integer(), nullable=False),
        sa.Column("difficulty", sa.String(), server_default=sa.text("'medium'")),
        sa.Column("selected_idx", sa.Integer()),
    )
    op.create_index(
        "ix_test_questions_test", "test_questions", ["test_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_test_questions_test", table_name="test_questions")
    op.drop_table("test_questions")
    op.drop_index("ix_tests_session_book", table_name="tests")
    op.drop_table("tests")
    op.drop_column("books", "llm_calls")
    op.drop_column("books", "total_tokens")
    op.drop_column("books", "completion_tokens")
    op.drop_column("books", "prompt_tokens")

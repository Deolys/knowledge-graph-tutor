"""initial schema: pgvector + books/chapters/concepts/relations/questions/progress

Revision ID: 001_initial
Revises:
Create Date: 2026-06-09
"""
import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "books",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "chapters",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "book_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id"), nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("order_num", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text()),
        sa.Column("status", sa.String(), server_default=sa.text("'pending'")),
    )

    op.create_table(
        "concepts",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "book_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id"), nullable=False,
        ),
        sa.Column(
            "chapter_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chapters.id"), nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("formula", sa.Text()),
        sa.Column("quote", sa.Text()),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(384)),
        sa.Column("canonical_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "relations",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "from_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("concepts.id"), nullable=False,
        ),
        sa.Column(
            "to_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("concepts.id"), nullable=False,
        ),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "is_cross_chapter", sa.Boolean(), server_default=sa.text("false")
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "questions",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "concept_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("concepts.id"), nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=False),
        sa.Column("correct_idx", sa.Integer(), nullable=False),
        sa.Column("difficulty", sa.String(), server_default=sa.text("'medium'")),
    )

    op.create_table(
        "progress",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column(
            "concept_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("concepts.id"), nullable=False,
        ),
        sa.Column(
            "status", sa.String(), server_default=sa.text("'not_started'")
        ),
        sa.Column("score", sa.Float()),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0")),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now()
        ),
    )

    # Индексы (см. SQL-схему в knowledge_graph_analytics.md)
    op.execute(
        "CREATE INDEX ix_concepts_embedding ON concepts "
        "USING ivfflat (embedding vector_cosine_ops)"
    )
    op.create_index(
        "ix_progress_session_concept", "progress", ["session_id", "concept_id"]
    )
    op.create_index("ix_relations_from_to", "relations", ["from_id", "to_id"])


def downgrade() -> None:
    op.drop_index("ix_relations_from_to", table_name="relations")
    op.drop_index("ix_progress_session_concept", table_name="progress")
    op.execute("DROP INDEX IF EXISTS ix_concepts_embedding")
    op.drop_table("progress")
    op.drop_table("questions")
    op.drop_table("relations")
    op.drop_table("concepts")
    op.drop_table("chapters")
    op.drop_table("books")

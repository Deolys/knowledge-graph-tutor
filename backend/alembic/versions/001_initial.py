"""initial schema v2: ontology tables + books/chapters/entities/relations/questions/progress

Revision ID: 001_initial
Revises:
Create Date: 2026-06-11
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

    # ─── Онтология (синхронизируется из ontology.yaml) ───
    op.create_table(
        "entity_types",
        sa.Column("type_name", sa.String(), primary_key=True),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("attrs", postgresql.JSONB(), nullable=False),
        sa.Column("color", sa.String(), nullable=False),
        sa.Column("tier", sa.String(), nullable=False),
    )

    op.create_table(
        "relation_types",
        sa.Column("type_name", sa.String(), primary_key=True),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("domain_types", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("range_types", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column(
            "is_transitive", sa.Boolean(), server_default=sa.text("false")
        ),
        sa.Column(
            "is_symmetric", sa.Boolean(), server_default=sa.text("false")
        ),
        sa.Column(
            "traversal_weight", sa.Float(), server_default=sa.text("0.5")
        ),
    )

    op.create_table(
        "profiles",
        sa.Column("profile_name", sa.String(), primary_key=True),
        sa.Column(
            "entity_types", postgresql.ARRAY(sa.String()), nullable=False
        ),
    )

    # ─── Книги ───
    op.create_table(
        "books",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column(
            "profile", sa.String(),
            sa.ForeignKey("profiles.profile_name"),
            server_default=sa.text("'universal'"),
        ),
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
            sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("order_num", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text()),
        sa.Column("status", sa.String(), server_default=sa.text("'pending'")),
    )

    # ─── Сущности (типизированные узлы) ───
    op.create_table(
        "entities",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "book_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "chapter_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chapters.id"),
        ),
        sa.Column(
            "entity_type", sa.String(),
            sa.ForeignKey("entity_types.type_name"), nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "attrs", postgresql.JSONB(), nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("source_quote", sa.Text()),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(384)),
        sa.Column("canonical_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ─── Связи (типизированные рёбра) ───
    op.create_table(
        "relations",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "book_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "from_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "to_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "relation_type", sa.String(),
            sa.ForeignKey("relation_types.type_name"), nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_quote", sa.Text(), nullable=False),
        sa.Column(
            "is_cross_chapter", sa.Boolean(), server_default=sa.text("false")
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("from_id", "to_id", "relation_type"),
    )

    op.create_table(
        "questions",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"), primary_key=True,
        ),
        sa.Column(
            "entity_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False,
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
            "entity_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "status", sa.String(), server_default=sa.text("'not_started'")
        ),
        sa.Column("score", sa.Float()),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "entity_id"),
    )

    # ─── Индексы ───
    op.execute(
        "CREATE INDEX ix_entities_embedding ON entities "
        "USING ivfflat (embedding vector_cosine_ops)"
    )
    op.create_index("ix_entities_book_type", "entities", ["book_id", "entity_type"])
    op.create_index(
        "ix_relations_from_type", "relations", ["from_id", "relation_type"]
    )
    op.create_index(
        "ix_relations_to_type", "relations", ["to_id", "relation_type"]
    )
    op.create_index(
        "ix_progress_session_entity", "progress", ["session_id", "entity_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_progress_session_entity", table_name="progress")
    op.drop_index("ix_relations_to_type", table_name="relations")
    op.drop_index("ix_relations_from_type", table_name="relations")
    op.drop_index("ix_entities_book_type", table_name="entities")
    op.execute("DROP INDEX IF EXISTS ix_entities_embedding")
    op.drop_table("progress")
    op.drop_table("questions")
    op.drop_table("relations")
    op.drop_table("entities")
    op.drop_table("chapters")
    op.drop_table("books")
    op.drop_table("profiles")
    op.drop_table("relation_types")
    op.drop_table("entity_types")

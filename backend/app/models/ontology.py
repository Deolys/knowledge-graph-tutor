"""ORM-модели онтологии: синхронизируются из ontology.yaml скриптом sync_ontology.

Эти таблицы — отражение YAML в БД: дают FK-целостность для entities/relations
и обслуживают /api/ontology. Источник правды — YAML, не эти строки.
"""
from sqlalchemy import Boolean, Float, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class EntityTypeRow(Base):
    __tablename__ = "entity_types"

    type_name: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    attrs: Mapped[list] = mapped_column(JSONB, nullable=False)
    color: Mapped[str] = mapped_column(String, nullable=False)
    tier: Mapped[str] = mapped_column(String, nullable=False)


class RelationTypeRow(Base):
    __tablename__ = "relation_types"

    type_name: Mapped[str] = mapped_column(String, primary_key=True)
    label: Mapped[str] = mapped_column(String, nullable=False)
    domain_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    range_types: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    is_transitive: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )
    is_symmetric: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false")
    )
    traversal_weight: Mapped[float] = mapped_column(
        Float, server_default=text("0.5")
    )


class ProfileRow(Base):
    __tablename__ = "profiles"

    profile_name: Mapped[str] = mapped_column(String, primary_key=True)
    entity_types: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False
    )

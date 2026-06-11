"""Схемы онтологии — для легенды, фильтров и выбора профиля в UI."""
from pydantic import BaseModel


class EntityTypeOut(BaseModel):
    type_name: str
    label: str
    description: str
    attrs: list[str]
    color: str
    tier: str


class RelationTypeOut(BaseModel):
    type_name: str
    label: str
    domain_types: list[str]
    range_types: list[str]
    is_transitive: bool
    is_symmetric: bool
    traversal_weight: float


class ProfileOut(BaseModel):
    profile_name: str
    entity_types: list[str]


class OntologyOut(BaseModel):
    version: str
    entity_types: list[EntityTypeOut]
    relation_types: list[RelationTypeOut]
    profiles: list[ProfileOut]

"""Загрузка онтологии из YAML в Pydantic-модели.

Онтология — единственный источник правды о типах сущностей и отношений.
YAML загружается один раз и кэшируется. `sync_ontology.py` переносит эти же
данные в БД (FK-целостность, выдача через /api/ontology), но runtime-логика
(промпты, валидация, обход графа) читает онтологию отсюда.
"""
from __future__ import annotations

import functools
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, PrivateAttr

_ONTOLOGY_PATH = Path(__file__).parent / "ontology.yaml"
_TEMPLATES_PATH = Path(__file__).parent / "traversal_templates.yaml"


class EntityType(BaseModel):
    type_name: str
    label: str
    description: str
    attrs: list[str] = Field(default_factory=list)
    color: str
    tier: str


class RelationType(BaseModel):
    type_name: str
    label: str
    domain_types: list[str]
    range_types: list[str]
    is_transitive: bool = False
    is_symmetric: bool = False
    traversal_weight: float = 0.5

    def active_domain(self, profile: "Profile") -> list[str]:
        active = set(profile.entity_types)
        return [t for t in self.domain_types if t in active]

    def active_range(self, profile: "Profile") -> list[str]:
        active = set(profile.entity_types)
        return [t for t in self.range_types if t in active]

    def is_active(self, profile: "Profile") -> bool:
        """Отношение активно, если И domain И range пересекаются с профилем."""
        return bool(self.active_domain(profile)) and bool(
            self.active_range(profile)
        )


class Profile(BaseModel):
    profile_name: str
    entity_types: list[str]

    _ontology: "Ontology | None" = PrivateAttr(default=None)

    def bind(self, ontology: "Ontology") -> "Profile":
        self._ontology = ontology
        return self

    def active_entity_types(self) -> list[EntityType]:
        assert self._ontology is not None
        return [
            self._ontology.entity_types[t]
            for t in self.entity_types
            if t in self._ontology.entity_types
        ]

    def active_relation_types(self) -> list[RelationType]:
        assert self._ontology is not None
        return [
            rt
            for rt in self._ontology.relation_types.values()
            if rt.is_active(self)
        ]


class TraversalStep(BaseModel):
    relation: str
    direction: str  # out | in | both
    depth: int = 1


class TraversalTemplate(BaseModel):
    name: str
    match_types: list[str]
    expand: list[TraversalStep]


class Ontology(BaseModel):
    version: str
    entity_types: dict[str, EntityType]
    relation_types: dict[str, RelationType]
    profiles: dict[str, Profile]
    templates: dict[str, TraversalTemplate] = Field(default_factory=dict)

    def profile(self, name: str) -> Profile:
        prof = self.profiles.get(name) or self.profiles["universal"]
        return prof.bind(self)


@functools.lru_cache(maxsize=1)
def load_ontology() -> Ontology:
    raw = yaml.safe_load(_ONTOLOGY_PATH.read_text(encoding="utf-8"))

    entity_types = {
        name: EntityType(type_name=name, **body)
        for name, body in raw["entity_types"].items()
    }
    relation_types = {
        name: RelationType(
            type_name=name,
            label=body["label"],
            domain_types=body["domain"],
            range_types=body["range"],
            is_transitive=body.get("transitive", False),
            is_symmetric=body.get("symmetric", False),
            traversal_weight=body.get("traversal_weight", 0.5),
        )
        for name, body in raw["relation_types"].items()
    }
    profiles = {
        name: Profile(profile_name=name, entity_types=body["entity_types"])
        for name, body in raw["profiles"].items()
    }

    templates: dict[str, TraversalTemplate] = {}
    if _TEMPLATES_PATH.exists():
        traw = yaml.safe_load(_TEMPLATES_PATH.read_text(encoding="utf-8")) or {}
        templates = {
            name: TraversalTemplate(
                name=name,
                match_types=body["match_types"],
                expand=[TraversalStep(**s) for s in body["expand"]],
            )
            for name, body in traw.items()
        }

    ontology = Ontology(
        version=raw["version"],
        entity_types=entity_types,
        relation_types=relation_types,
        profiles=profiles,
        templates=templates,
    )
    for prof in ontology.profiles.values():
        prof.bind(ontology)
    return ontology

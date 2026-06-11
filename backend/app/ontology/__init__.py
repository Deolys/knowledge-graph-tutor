"""Онтологический слой: типы сущностей/отношений, профили, обход графа."""
from app.ontology.loader import (
    EntityType,
    Ontology,
    Profile,
    RelationType,
    TraversalStep,
    TraversalTemplate,
    load_ontology,
)

__all__ = [
    "EntityType",
    "Ontology",
    "Profile",
    "RelationType",
    "TraversalStep",
    "TraversalTemplate",
    "load_ontology",
]

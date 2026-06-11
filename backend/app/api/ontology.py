"""Роутер онтологии: активная онтология и список профилей для UI."""
from fastapi import APIRouter

from app.ontology import load_ontology
from app.schemas.ontology import (
    EntityTypeOut,
    OntologyOut,
    ProfileOut,
    RelationTypeOut,
)

router = APIRouter(prefix="/api/ontology", tags=["ontology"])


def _ontology_out() -> OntologyOut:
    ont = load_ontology()
    return OntologyOut(
        version=ont.version,
        entity_types=[
            EntityTypeOut(
                type_name=et.type_name,
                label=et.label,
                description=et.description,
                attrs=et.attrs,
                color=et.color,
                tier=et.tier,
            )
            for et in ont.entity_types.values()
        ],
        relation_types=[
            RelationTypeOut(
                type_name=rt.type_name,
                label=rt.label,
                domain_types=rt.domain_types,
                range_types=rt.range_types,
                is_transitive=rt.is_transitive,
                is_symmetric=rt.is_symmetric,
                traversal_weight=rt.traversal_weight,
            )
            for rt in ont.relation_types.values()
        ],
        profiles=[
            ProfileOut(profile_name=p.profile_name, entity_types=p.entity_types)
            for p in ont.profiles.values()
        ],
    )


@router.get("", response_model=OntologyOut)
async def get_ontology() -> OntologyOut:
    """Активная онтология — для легенды, цветов узлов и фильтров."""
    return _ontology_out()


@router.get("/profiles", response_model=list[ProfileOut])
async def get_profiles() -> list[ProfileOut]:
    ont = load_ontology()
    return [
        ProfileOut(profile_name=p.profile_name, entity_types=p.entity_types)
        for p in ont.profiles.values()
    ]

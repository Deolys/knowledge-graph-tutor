import { create } from "zustand";
import type { EntityType, Ontology, RelationType } from "../types";
import { getOntology } from "../api/ontology";

interface OntologyState {
  ontology: Ontology | null;
  entityTypes: Record<string, EntityType>;
  relationTypes: Record<string, RelationType>;
  loaded: boolean;
  load: () => Promise<void>;
}

export const useOntologyStore = create<OntologyState>((set, get) => ({
  ontology: null,
  entityTypes: {},
  relationTypes: {},
  loaded: false,
  load: async () => {
    if (get().loaded) return;
    const ontology = await getOntology();
    const entityTypes: Record<string, EntityType> = {};
    for (const et of ontology.entity_types) entityTypes[et.type_name] = et;
    const relationTypes: Record<string, RelationType> = {};
    for (const rt of ontology.relation_types) relationTypes[rt.type_name] = rt;
    set({ ontology, entityTypes, relationTypes, loaded: true });
  },
}));

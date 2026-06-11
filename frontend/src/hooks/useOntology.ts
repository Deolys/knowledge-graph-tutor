import { useEffect } from "react";
import { useOntologyStore } from "../store/ontologyStore";

export function useOntology() {
  const { ontology, entityTypes, relationTypes, loaded, load } =
    useOntologyStore();

  useEffect(() => {
    load();
  }, [load]);

  return { ontology, entityTypes, relationTypes, loaded };
}

import { client } from "./client";
import type { Ontology, Profile } from "../types";

export async function getOntology(): Promise<Ontology> {
  const { data } = await client.get<Ontology>("/api/ontology");
  return data;
}

export async function getProfiles(): Promise<Profile[]> {
  const { data } = await client.get<Profile[]>("/api/ontology/profiles");
  return data;
}

import { parseUnit, type RaceConfig } from "../config/schema";

// Config-driven units [F4c]: every race is a validated JSON config under config/races/.
// import.meta.glob bakes them at build (SSG) — no DB on the read path [O6a].
const modules = import.meta.glob("../config/races/*.json", { eager: true });

export function allRaces(): RaceConfig[] {
  return Object.values(modules)
    .map((m) => parseUnit((m as { default: unknown }).default) as RaceConfig)
    .sort((a, b) => a.id.localeCompare(b.id));
}

// Colorblind-safe party palette lives ONLY in data viz [C4a,C5a]; map party -> token class.
const PARTY_CLASS: Record<string, string> = {
  D: "bg-party-dem",
  R: "bg-party-rep",
};
export function partyColorClass(party: string): string {
  return PARTY_CLASS[party] ?? "bg-party-ind";
}

const PARTY_LABEL: Record<string, string> = {
  D: "Democrat",
  R: "Republican",
  I: "Independent",
  L: "Libertarian",
  G: "Green",
};
export function partyLabel(party: string): string {
  return PARTY_LABEL[party] ?? "Other";
}

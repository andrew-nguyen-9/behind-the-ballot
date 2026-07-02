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

// Colorblind pattern mapping [C5a, Q4.2]: Dem=solid, Rep=diagonal hatch, Ind=dots,
// Other=crosshatch. Overlaid on the party color so viz stays distinguishable in grayscale.
// Single source of truth — drives both the CSS overlay class (pure-CSS bars/swatches) and
// the SVG <pattern> fill (W1 maps, via PartyPatternDefs.astro).
export type PartyPatternKind = "solid" | "hatch" | "dots" | "crosshatch";
const PARTY_PATTERN: Record<string, PartyPatternKind> = {
  D: "solid",
  R: "hatch",
  I: "dots",
};
export function partyPatternKind(party: string): PartyPatternKind {
  return PARTY_PATTERN[party] ?? "crosshatch";
}
// CSS overlay class for pure-CSS viz (PartySwatch/PartyBar). Solid => no class ("").
export function partyPatternClass(party: string): string {
  const kind = partyPatternKind(party);
  return kind === "solid" ? "" : `pf-${kind}`;
}
// SVG fill reference for map shapes (W1) — pairs with <PartyPatternDefs>. Solid => undefined
// (fill the shape with the plain party color instead).
export function partyPatternFill(party: string): string | undefined {
  const kind = partyPatternKind(party);
  return kind === "solid" ? undefined : `url(#pf-${kind})`;
}

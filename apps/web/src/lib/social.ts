// Curated official social profiles [E-6], baked by pipeline sources/social.py. Read at build.
// Static links + baked metadata ONLY — NO platform API, NO runtime JS, NO tracking, NO live
// embeds (spec invariant). Provenance is the "Curated official-handle" row in
// docs/03_DATA_SOURCES.md [R14a]. Fixtures live in src/data/social/*.json; an absent/empty set
// renders honest-empty. Consumed by <SocialBlock> (and E-5 dashboards later).
const mods = import.meta.glob("../data/social/*.json", { eager: true });

export interface SocialProfile {
  entity_id: string; // bioguide / candidate id / race-candidate slug
  entity_name: string;
  role: string; // "candidate" | "incumbent" | ...
  state: string; // USPS postal
  platform: string | null; // "x" | "instagram" | ... (null when no handle at all)
  handle: string | null; // null = honest-empty (unverified/absent)
  profile_url: string | null;
  latest_post_url: string | null;
  latest_post_at: string | null; // ISO-8601 timestamp
}

// A profile is renderable as a link only when it carries a verified handle + profile URL.
// Otherwise it is honest-empty — never a fabricated link [E-6].
export function isLinkable(p: SocialProfile): boolean {
  return Boolean(p.handle && p.profile_url);
}

// Only the linkable profiles from a set — what <SocialBlock> actually renders as links. Pure.
export function linkableProfiles(rows: SocialProfile[]): SocialProfile[] {
  return rows.filter(isLinkable);
}

// Official profiles for one entity (candidate/incumbent), in source order. Pure + injectable so
// callers (SocialBlock, E-5 dashboards) and tests can pass their own rows. Defaults to the baked
// set. An entity with no verified handle yields rows whose isLinkable() is false → honest-empty.
export function socialForEntity(entityId: string, rows: SocialProfile[] = loadSocial()): SocialProfile[] {
  return rows.filter((r) => r.entity_id === entityId);
}

// Every baked social profile (flattened across fixture files). Empty when none are curated yet.
export function loadSocial(): SocialProfile[] {
  return Object.values(mods).flatMap((m) => (m as { default: SocialProfile[] }).default ?? []);
}

// Human platform label for a handle. Unknown/undefined platforms fall back to a generic label.
const PLATFORM_LABELS: Record<string, string> = {
  x: "X",
  twitter: "X",
  instagram: "Instagram",
  facebook: "Facebook",
  bluesky: "Bluesky",
  threads: "Threads",
  youtube: "YouTube",
  tiktok: "TikTok",
};
export function platformLabel(platform: string | null): string {
  if (!platform) return "Profile";
  return PLATFORM_LABELS[platform.toLowerCase()] ?? platform;
}

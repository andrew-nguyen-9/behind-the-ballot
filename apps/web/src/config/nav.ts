// Site shell navigation + footer contract [E0.5]. Single source for the header nav,
// the footer link columns, and the two external anchors (an9.dev + the project repo).
// Kept as plain data so it's unit-testable and shared by header (Layout) and footer.

export interface NavLink {
  href: string;
  label: string;
  /** external => rendered target=_blank rel=noopener + visual affordance. */
  external?: boolean;
}

export interface FooterColumn {
  title: string;
  links: NavLink[];
}

// External anchors [Q5.1/Q5.2]. Site lives on the ballot.an9.dev subdomain; the footer
// links back to the an9.dev hub and out to the source repo.
export const AN9_URL = "https://an9.dev";
export const AN9_LABEL = "Back to an9.dev";
export const REPO_URL = "https://github.com/andrew-nguyen-9/behind-the-ballot";

// Primary header nav (Home is the logo, so it's not repeated here).
export const primaryNav: readonly NavLink[] = [
  { href: "/races", label: "Races" },
  { href: "/members", label: "Members" },
  { href: "/chamber", label: "Chamber" },
  { href: "/senate", label: "Senate" },
  { href: "/forecast", label: "Forecast" },
  { href: "/gerrymander", label: "Maps" },
  { href: "/articles", label: "Articles" },
  { href: "/search", label: "Search" },
];

// Footer link columns [Q5.2]: Races, Members, Forecast, Sources, Methodology, Articles +
// GitHub. Methodology has no dedicated route — it points at /forecast, matching the
// existing in-page convention (races/[id] links "methodology" -> /forecast).
export const footerColumns: readonly FooterColumn[] = [
  {
    title: "Tracking",
    links: [
      { href: "/races", label: "Races" },
      { href: "/members", label: "Members" },
      { href: "/forecast", label: "Forecast" },
    ],
  },
  {
    title: "Understand",
    links: [
      { href: "/sources", label: "Sources" },
      { href: "/demographics", label: "Demographics" },
      { href: "/forecast", label: "Methodology" },
      { href: "/articles", label: "Articles" },
    ],
  },
  {
    title: "Project",
    links: [{ href: REPO_URL, label: "GitHub", external: true }],
  },
];

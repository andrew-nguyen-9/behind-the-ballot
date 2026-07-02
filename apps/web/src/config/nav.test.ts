import { describe, expect, it } from "vitest";
import {
  AN9_URL,
  REPO_URL,
  footerColumns,
  primaryNav,
} from "./nav";

const allFooterLinks = footerColumns.flatMap((c) => c.links);

describe("primaryNav", () => {
  it("omits Home (the logo is the home link)", () => {
    expect(primaryNav.some((l) => l.href === "/")).toBe(false);
  });
  it("uses internal absolute paths only", () => {
    for (const l of primaryNav) expect(l.href.startsWith("/")).toBe(true);
  });
});

describe("footerColumns", () => {
  it("covers the required link set [Q5.2]", () => {
    const labels = allFooterLinks.map((l) => l.label);
    for (const required of [
      "Races",
      "Members",
      "Forecast",
      "Sources",
      "Methodology",
      "Articles",
      "GitHub",
    ]) {
      expect(labels).toContain(required);
    }
  });
  it("marks only the repo link external and points it at the repo", () => {
    const external = allFooterLinks.filter((l) => l.external);
    expect(external).toHaveLength(1);
    expect(external[0].href).toBe(REPO_URL);
  });
  it("keeps internal footer links as absolute paths", () => {
    for (const l of allFooterLinks) {
      if (!l.external) expect(l.href.startsWith("/")).toBe(true);
    }
  });
});

describe("external anchors", () => {
  it("an9.dev + repo are https absolute URLs", () => {
    expect(AN9_URL).toMatch(/^https:\/\//);
    expect(REPO_URL).toMatch(/^https:\/\/github\.com\//);
  });
});

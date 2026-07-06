import { describe, expect, it } from "vitest";
import {
  isLinkable,
  linkableProfiles,
  loadSocial,
  platformLabel,
  socialForEntity,
  type SocialProfile,
} from "./social";

const linked: SocialProfile = {
  entity_id: "AZ-gov-1",
  entity_name: "Jane Doe",
  role: "candidate",
  state: "AZ",
  platform: "x",
  handle: "janedoe",
  profile_url: "https://x.com/janedoe",
  latest_post_url: "https://x.com/janedoe/status/1",
  latest_post_at: "2026-07-01T12:00:00+00:00",
};
const empty: SocialProfile = {
  entity_id: "AZ-gov-1",
  entity_name: "Jane Doe",
  role: "candidate",
  state: "AZ",
  platform: null,
  handle: null,
  profile_url: null,
  latest_post_url: null,
  latest_post_at: null,
};

describe("social", () => {
  it("treats a verified handle+URL as linkable, an unset handle as honest-empty", () => {
    expect(isLinkable(linked)).toBe(true);
    expect(isLinkable(empty)).toBe(false);
    // a handle with no URL is NOT linkable (never a fabricated link)
    expect(isLinkable({ ...empty, handle: "janedoe" })).toBe(false);
  });

  it("filters a set down to only its linkable profiles", () => {
    expect(linkableProfiles([linked, empty])).toEqual([linked]);
    expect(linkableProfiles([empty])).toEqual([]); // honest-empty
  });

  it("selects an entity's profiles from an injected set", () => {
    const rows = [linked, { ...empty, entity_id: "AZ-sen-9" }];
    expect(socialForEntity("AZ-gov-1", rows)).toEqual([linked]);
    expect(socialForEntity("no-such-entity", rows)).toEqual([]);
  });

  it("labels platforms, falling back for unknown/absent", () => {
    expect(platformLabel("x")).toBe("X");
    expect(platformLabel("instagram")).toBe("Instagram");
    expect(platformLabel(null)).toBe("Profile");
    expect(platformLabel("mastodon")).toBe("mastodon");
  });

  it("loads the baked set (honest-empty until real handles are curated)", () => {
    const all = loadSocial();
    expect(Array.isArray(all)).toBe(true);
    for (const p of all) {
      // every baked row is internally consistent: a link implies a handle
      if (isLinkable(p)) expect(p.handle).toBeTruthy();
    }
  });
});

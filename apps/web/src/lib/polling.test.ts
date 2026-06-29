import { describe, expect, it } from "vitest";
import { pollingForRace } from "./polling";

describe("polling", () => {
  // Polling is DROPPED from V1 (no clean open feed post-538; see docs/BACKLOG.md). No polling
  // artifacts ship, so every lookup is null and the race page hides the polling section.
  it("returns null (polling deferred to V1.1)", () => {
    expect(pollingForRace("us-senate-2026-TX")).toBeNull();
    expect(pollingForRace("no-such-race-9999")).toBeNull();
  });
});

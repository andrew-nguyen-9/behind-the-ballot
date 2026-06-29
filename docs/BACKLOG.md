# Backlog (post-V1)

Items deferred out of V1 scope. New ideas land here, not in V1 `[scope discipline]`.

## Polling source (deferred from V1 — decision iter 66)
538's public poll CSVs were discontinued post-ABC (verified iter 60: endpoints serve an HTML
shell; last real update Sept 2024). No open aggregator has both a machine-readable feed AND a
clean reuse license (checked: PollingSource = paid/no-redistribution; USPollingData = no API;
RCP/270toWin/RacetotheWH = proprietary; DDHQ/Silver Bulletin = paid). **Decision: ship V1
without live polling.** The forecast already degrades to fundamentals-only (`blend_margin(None,…)`,
tested) and the polling UI hides when the artifact is empty (`races/[id].astro` guard) — no code
change needed. Connectors (`sources/polls.py`, `pollster_ratings.py`) are kept; they bake the
moment a working source exists.

**V1.1 task:** secure a polling source, then either repoint `polls.py`/`pollster_ratings.py`
(if CSV/API) or build a new connector. Candidates to revisit: Wikipedia race tables (CC BY-SA,
attribute) · a licensed feed (PollingSource/DDHQ) if ToS permits republishing derived averages.

## Cross-party cosponsorship index (v1.6.4 follow-up)
Sponsorship COUNTS shipped (iter 65). The cross-party index `[M7a]` needs each bill's cosponsor
parties (a per-bill fan-out over Congress.gov) — deferred.

## Senate roll-call votes (v1.6.2 follow-up)
House roll-call list shipped (iter 63). Senate roll calls aren't in the Congress.gov API →
needs a GovTrack/senate.gov XML slice. Per-member vote positions (missed-votes) also follow-up.

// The DATA_SOURCES contract surfaced to readers [R14a]. Mirrors docs/03_DATA_SOURCES.md
// and the pipeline integrity registry — every published figure traces to a row here.
export interface Source {
  label: string;
  provider: string;
  url: string;
  license: string;
  cadence: string;
  freshnessFloor: string;
  modules: string;
}

export const SOURCES: Source[] = [
  { label: "Campaign finance", provider: "OpenFEC + FEC bulk", url: "https://api.open.fec.gov", license: "US public domain", cadence: "weekly", freshnessFloor: "14 days", modules: "Finance, tracker" },
  { label: "Polls", provider: "538 polls CSV", url: "https://projects.fivethirtyeight.com/polls/", license: "538 terms (attributed)", cadence: "daily", freshnessFloor: "3 days", modules: "Polling, forecast" },
  { label: "Pollster ratings", provider: "538 pollster ratings", url: "https://projects.fivethirtyeight.com/pollster-ratings/", license: "538 terms (attributed)", cadence: "weekly", freshnessFloor: "30 days", modules: "Polling" },
  { label: "Demographics", provider: "US Census ACS", url: "https://www.census.gov/programs-surveys/acs", license: "US public domain", cadence: "yearly", freshnessFloor: "400 days", modules: "Demographics, forecast" },
  { label: "District geography", provider: "Census TIGER/Line", url: "https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html", license: "US public domain", cadence: "yearly + court orders", freshnessFloor: "event-driven", modules: "Gerrymander, maps" },
  { label: "Address lookup", provider: "Census Geocoder", url: "https://geocoding.geo.census.gov", license: "US public domain", cadence: "on request (cached)", freshnessFloor: "30-day cache", modules: "Find my district" },
  { label: "Members of Congress", provider: "congress-legislators + Congress.gov", url: "https://github.com/unitedstates/congress-legislators", license: "CC0 / US public domain", cadence: "weekly", freshnessFloor: "14 days", modules: "Members, caucus" },
  { label: "Roll-call votes", provider: "Congress.gov + GovTrack", url: "https://www.congress.gov", license: "US public domain / GovTrack terms", cadence: "daily (in session)", freshnessFloor: "7 days", modules: "Member analytics" },
  { label: "Ideology", provider: "Voteview DW-NOMINATE", url: "https://voteview.com", license: "Academic, free (attributed)", cadence: "per Congress", freshnessFloor: "event-driven", modules: "Member analytics" },
];

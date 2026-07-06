# Voice — writing & microcopy

Load with `INDEX.md` for any copy/label/microcopy task. Numbers speak; chrome recedes.

## Tone

**Neutral, precise, quietly confident.** We report; we do not editorialize. A Swiss-typography
sensibility in words: precision, neutrality, trust. No hype, no partisanship, no drama. If a
sentence is doing persuasion, cut it — the data persuades.

## Honesty about certainty (non-negotiable)

Never imply certainty we don't have. These are **first-class UI, not footnotes**:

- `provisional` · `% reporting` · `as-of <date>` · `estimated` · `projected` · `unofficial`.
- A forecast is a probability, never a promise — say "favored", "leans", "% chance", not "will win".
- If a figure is stale past its freshness floor, it is **flagged or hidden — never shown
  silently** (data contract, `docs/03_DATA_SOURCES.md`).
- Honest-empty over fake data: "No sourced data yet" (`EmptyState`), never a placeholder number.

## Neutrality

- **No single-verdict framing.** Present multiple metrics with caveats; let the reader weigh.
- Party names/colors are descriptive, never evaluative. Party colors stay in data-viz only.
- Attribute every claim to its source; link it. "According to <source>, as of <date>."

## Mechanics

- Sentence case for UI labels and most headings; title case only for proper nouns.
- Numbers: tabular figures (`.tnum`) in tables/results; thousands separators; explicit units and
  as-of dates. Percentages to the precision the source supports — no false precision.
- Prefer plain words over jargon; expand an acronym on first use.
- Active, short. Say what a control does, not how it feels.

## Examples

- Yes: "Republicans favored for Senate control (58% in the current model)."
  No: "Republicans are set to take the Senate."
- Yes: "62% reporting · provisional."  No: a final-looking bar with no caveat.
- Yes: "No sourced polling for this race yet."  No: "0%" where there is simply no data.

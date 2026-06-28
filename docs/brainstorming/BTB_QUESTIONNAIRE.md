# Behind the Ballot — V1 Scope & Build Questionnaire (300 MCQs)

Front-load every decision so planning + autonomous build are unblocked. Convention
(same as metrotrack): pick **one** letter per question; `⭐` = my recommended default
given the locked priors below. Add notes after `→`. **"Other" is always allowed.**
**Skip what you don't care about → you accept the ⭐.**

Answers that survive graduate into `docs/phases/v1/`, `design-system/`, ADRs, and
`DATA_SOURCES.md`. Each locked decision will cite its question id, e.g. `[E3a]`.

**Locked priors (the lens for every ⭐):**
- **Hobbyist budget — free tier on *everything*** (storage, APIs, hosting, email, CI).
- **Skill-expansion for hireability** is a first-class goal — diversify the stack.
- **Strict non-partisan neutrality** — this is an election site; credibility = sourced,
  dated, methodology-transparent, no editorializing on outcomes.
- **2026 US midterms first**, but architected for *every future election* (config-driven races).
- **Federal focus + high-level State view** for now.
- **Autonomous loops** (ralph-loop + GitHub Actions) for build, QA, and self-emailed issues.
- **Token efficiency is king** — cold sub-agents driven by plan files, not chat context.

How to answer fast: skim, drop a letter after each `→`, skip the rest. ~30–45 min.

---

## A · Vision, positioning & scope (A1–A12)

**A1. The one-line job of Behind the Ballot?**
a) Non-partisan 2026 midterm tracker + analytics hub ⭐  b) Election *forecasting* model (538-style)  c) Civic-data portfolio showcase  d) Data-journalism publication
→ All the above with a focus on A, B, and D

**A2. Primary success metric for V1?**
a) Breadth of working analytics modules ⭐  b) Forecast accuracy vs outcomes  c) Organic search traffic  d) Portfolio depth (skills demonstrated)
→ A

**A3. Editorial stance (non-negotiable for trust)?**
a) Strictly neutral, just-the-data + sourced ⭐  b) Neutral analysis w/ explainer commentary  c) Data-journalism w/ bylined takes
→ A for most. There will be B/C for the articles and findings section but I would like to be as neutral as possible

**A4. Scope at launch?**
a) Federal (House+Senate) + high-level state ⭐  b) Federal only  c) Federal + full state legislatures  d) Single proof race first
→ A

**A5. The headline V1 deliverable?**
a) Live race tracker + finance + polling + a forecast ⭐  b) Just the tracker + maps  c) Just the forecast model  d) Everything, sequenced
→ A

**A6. Time horizon V1 must serve?**
a) Now → Nov 2026 election night ⭐  b) Through 2026 primaries only  c) Build evergreen, 2026 is the demo
→ C

**A7. Reusability ambition?**
a) Config-driven for *any* future election (1 file = 1 race) ⭐  b) 2026-specific, generalize later  c) Hard-code 2026
→ A

**A8. V1 explicitly EXCLUDES…?**
a) User accounts/auth  b) Real-time election-night call engine  c) Paid tiers  d) Non-US elections  e) All of these ⭐
→ E

**A9. Public name?**
a) "Behind the Ballot" (keep repo name) ⭐  b) Shorter coinage (e.g. "Ballotwise")  c) Decide later
→ A

**A10. Domain?**
a) Subdomain of your stack, e.g. `ballot.an9.dev` ⭐  b) New domain `behindtheballot.*`  c) Free `*.pages.dev`/`*.vercel.app` for V1
→ A

**A11. Launch readiness bar = "V1 done"?**
a) Tracker+finance+polling+forecast live, all sourced + Lighthouse ≥90 ⭐  b) Tracker only  c) Per-module configurable
→ A

**A12. Risk posture on data gaps?**
a) Degrade gracefully — hide a module, log the gap ⭐  b) Block launch until parity  c) Show "data unavailable" placeholders
→ A

---

## B · Brand, voice & neutrality guardrails (B1–B12)

**B1. Tone of copy?**
a) Clear/civic/plain ⭐  b) Sharp/explanatory  c) Wonky/data-dense  d) Approachable/friendly
→ A

**B2. How do you signal neutrality structurally?**
a) Every figure → source + "as of" date + methodology link ⭐  b) An About/Bias-statement page  c) Both A+B ⭐  d) Don't over-engineer it
→ C

**B3. Handling of party framing in UI?**
a) Consistent neutral colors + always both/all parties shown ⭐  b) Standard red/blue  c) Colorblind-safe non-red/blue palette ⭐
→ A with option for C

**B4. Forecast probabilities — how framed to avoid misread?**
a) Always show range + "not a prediction" + methodology ⭐  b) Single number  c) Hide forecast, show inputs only
→ A

**B5. Do you take a position on any race?**
a) Never — model + data speak ⭐  b) Editor's note on notable races  c) Allow opinion articles clearly labeled
→ A

**B6. Comment/engagement features?**
a) None in V1 (no moderation burden) ⭐  b) Reactions only  c) Comments (deferred)
→ A

**B7. Correction policy?**
a) Public changelog + "corrected on" notes ⭐  b) Silent fixes  c) Git history is the record
→ A

**B8. Source transparency level?**
a) `DATA_SOURCES.md` + per-figure citation links ⭐  b) Sources page only  c) Footnotes per page
→ A

**B9. Disclaimer on forecasts/polls?**
a) Standing disclaimer + per-module ⭐  b) One global disclaimer  c) None
→ A

**B10. Voice on social/articles?**
a) Factual, "here's what changed" ⭐  b) Analytical hot-takes  c) No social presence V1
→ A

**B11. Brand personality?**
a) Trustworthy/institutional ⭐  b) Modern/techy  c) Newsroom/urgent
→ A

**B12. Accessibility of language (reading level)?**
a) Plain-language, jargon defined in glossary ⭐  b) Assume political literacy  c) Two modes (simple/expert)
→ A

---

## C · Logo & design system (C1–C14)

**C1. Logo direction?**
a) Mark from civic iconography (ballot/check/ballot-box) ⭐  b) Wordmark only  c) Map/district-fragment motif  d) Abstract data motif
→ A

**C2. How do we generate the logo?**
a) Claude Design MCP — brainstorm variants, import `.dc.html` (as metrotrack did) ⭐  b) Hand-code SVG  c) Generate via image model then trace
→ A

**C3. Logo assets needed at V1?**
a) Header + footer + favicon + OG default + app icon ⭐  b) Header + favicon only  c) Full kit + per-module marks
→ A + C

**C4. Color system base?**
a) Neutral civic palette, party colors *only* in data viz ⭐  b) Patriotic red/white/blue  c) Monochrome + one accent
→ A

**C5. Party color encoding (data viz)?**
a) Colorblind-safe blue/red + patterns for safety ⭐  b) Standard blue/red  c) Purple-gradient (margin) instead of binary
→ A with C

**C6. Theme?**
a) Light-default + dark toggle ⭐  b) Dark-native + toggle  c) Light only V1
→ A

**C7. Typography?**
a) One readable sans + one serif for articles ⭐  b) Single variable font  c) System fonts (zero load)
→ A

**C8. Design-system home?**
a) Tokens file + small component lib (Storybook deferred) ⭐  b) Tailwind config only  c) Full Storybook now
→ C

**C9. Component library?**
a) shadcn/ui (Radix) — hireable, accessible ⭐  b) Hand-rolled  c) Headless UI  d) MUI/Chakra
→ A

**C10. Styling approach?**
a) Tailwind ⭐  b) CSS Modules  c) vanilla-extract  d) Plain CSS + tokens
→ A

**C11. Data-viz aesthetic?**
a) Clean/editorial (NYT/538 feel) ⭐  b) Dashboard/dense  c) Playful
→ A

**C12. Iconography?**
a) Lucide (open, consistent) ⭐  b) Heroicons  c) Custom set
→ A

**C13. Motion?**
a) Subtle, reduced-motion respected ⭐  b) Rich transitions  c) None
→ B

**C14. OG/share images?**
a) Auto-generated per page at build (race card → image) ⭐  b) One static OG  c) Manual per article
→ A

---

## D · Audience & personas (D1–D10)

**D1. #1 audience?**
a) Engaged voters / news consumers ⭐  b) Journalists/analysts  c) Recruiters viewing your portfolio  d) Political hobbyists/forecasters
→ A/B/D

**D2. Device priority?**
a) Mobile-first, desktop-excellent ⭐  b) Desktop-first (data-dense)
→ A

**D3. Reading depth assumption?**
a) Scan headline numbers, drill on demand ⭐  b) Deep readers  c) Both via progressive disclosure ⭐
→ C

**D4. Entry point most users hit?**
a) Homepage national dashboard ⭐  b) A specific race page (search/social)  c) An article
→ A

**D5. Geographic personalization?**
a) "Find your district" by address/ZIP ⭐  b) Pick from a list  c) None V1
→ A

**D6. Returning-user value?**
a) "What changed since you last looked" ⭐  b) Saved races (needs storage)  c) None V1
→ A

**D7. Notable secondary audience to design for?**
a) Educators/students ⭐  b) Campaign staff  c) Academics
→ A

**D8. Internationalization?**
a) English only V1 ⭐  b) Spanish too  c) i18n-ready scaffold, English content
→ A

**D9. Accessibility audience priority?**
a) Full WCAG 2.2 AA target ⭐  b) Best-effort  c) AA on core flows only
→ A

**D10. Portfolio framing (since hireability matters)?**
a) Subtle "built by" + linked case study ⭐  b) Prominent portfolio banner  c) None on the public site
→ A

---

## E · Feature modules & V1/later cut (E1–E20)

Rank the 10 named modules. ⭐ marks my proposed V1-vs-later split.

**E1. Election results / race tracking — V1?**
a) V1 core ⭐  b) Later
→ A

**E2. Campaign finance (FEC) — V1?**
a) V1 core ⭐  b) Later
→ A

**E3. Polling estimation/aggregation — V1?**
a) V1 core ⭐  b) Later
→ A

**E4. Election modeling/forecast — V1?**
a) V1 (heuristic forecast) ⭐  b) Later (after data modules)
→ A

**E5. Demographic analytics — V1?**
a) V1 (Census-backed) ⭐  b) Later
→ A

**E6. Issue analytics — V1?**
a) Later (data is fuzzy/expensive) ⭐  b) V1
→ A

**E7. Party demographic analytics — V1?**
a) Later (derived from E5) ⭐  b) V1
→ A

**E8. Gerrymandering analytics — V1?**
a) V1-lite (maps + compactness metrics) ⭐  b) Full V1  c) Later
→ A

**E9. Current party / caucus analytics — V1?**
a) V1 (chamber composition is easy + high-value) ⭐  b) Later
→ A

**E10. Congressional representative analytics — V1?**
a) V1 (member profiles, votes) ⭐  b) Later
→ A

**E11. The V1 module set, then?**
a) Tracker+Finance+Polling+Forecast+Demographics+Caucus+Members+Gerrymander-lite ⭐  b) Just tracker+finance+polling  c) All ten
→ A

**E12. What's the signature, "wow" module?**
a) The forecast (poll+fundamentals+sim) ⭐  b) Gerrymandering maps  c) Money-flow finance viz  d) Live results
→ A

**E13. Module that best shows hireable skill?**
a) Forecast model (stats/ML + sim) ⭐  b) Geospatial gerrymander maps  c) ETL pipeline  d) All, sequenced ⭐
→ A

**E14. Cross-module linking?**
a) Deep-link race ↔ finance ↔ polls ↔ member ↔ district ⭐  b) Siloed modules  c) Link later
→ A

**E15. National vs per-race default view?**
a) National dashboard → drill to race ⭐  b) Race-list first  c) Map first
→ A

**E16. Senate vs House vs Governor coverage in V1?**
a) Senate + House + key Governors ⭐  b) Senate + House  c) Senate only (35 races, tractable)
→ A

**E17. Primary elections coverage?**
a) Track results as they happen, light ⭐  b) Full primary analytics  c) General only
→ A
 
**E18. Ballot measures / referenda?**
a) Later ⭐  b) V1 high-level  c) Skip entirely
→ A

**E19. Historical elections (context)?**
a) Include 2018/2020/2022/2024 baselines ⭐  b) 2024 only  c) None
→ A

**E20. "Coming soon" treatment for later modules?**
a) Real indexable placeholder page per module ⭐  b) Hide entirely  c) Greyed nav item
→ A

---

## F · Election results & race tracking (F1–F14)

**F1. Result data source (general election)?**
a) AP/official where free + scrape state SoS + Wikipedia fallback ⭐  b) Paid AP/DDHQ  c) Single free source
→ A

**F2. Pre-election "result" = ?**
a) Status: race rating + last poll + finance, no fake numbers ⭐  b) Forecast %  c) Blank until polls close
→ A

**F3. Race ratings source?**
a) Aggregate Cook/Sabato/Inside (cite each) ⭐  b) Our own model only  c) One source
→ A

**F4. Race entity model?**
a) `races/<cycle>/<office>-<state>-<district>.toml` config ⭐  b) DB rows only  c) Both (config mirrors to DB) ⭐
→ A

**F5. Candidate data source?**
a) FEC (filers) + Ballotpedia/Wikipedia + Congress.gov for incumbents ⭐  b) Manual  c) One source
→ A

**F6. Live election-night handling V1?**
a) Periodic refresh (Action every N min) + manual fallback ⭐  b) Real-time websockets  c) Next-morning static update
→ A

**F7. Call/projection on election night?**
a) Mirror AP calls, never self-call ⭐  b) Our model calls  c) No calls, raw votes only
→ A

**F8. Vote-count display?**
a) % reporting + margin + raw, "as of" timestamp ⭐  b) Just winner  c) Full precinct detail
→ A

**F9. Uncalled/recount races?**
a) Clear "too close / pending" state ⭐  b) Show leader only  c) Hide
→ A

**F10. Race page anatomy?**
a) Candidates, rating, polls, money, district demo, history ⭐  b) Just candidates + result  c) Configurable
→ A

**F11. Incumbency / open-seat flags?**
a) Yes, computed from member data ⭐  b) Manual  c) Skip
→ A

**F12. Third-party / independent candidates?**
a) Show all qualified, neutral ⭐  b) Major + notable only  c) Major two only
→ A

**F13. Special elections (2025–26)?**
a) Track as they arise (config) ⭐  b) Skip  c) Retroactive only
→ A

**F14. Result provenance?**
a) Every race figure → source row + fetch timestamp ⭐  b) Source page  c) Trust the feed
→ A

---

## G · Campaign finance / FEC (G1–G14)

**G1. Primary finance source?**
a) OpenFEC API (api.open.fec.gov, free key via api.data.gov) ⭐  b) OpenSecrets API  c) FEC bulk downloads  d) A+C ⭐
→ D

**G2. Refresh cadence?**
a) Weekly (filings are periodic) ⭐  b) Nightly  c) On FEC filing deadlines
→ A

**G3. Finance metrics V1?**
a) Raised/spent/cash-on-hand/burn + top donors-by-type ⭐  b) Raised/spent only  c) Full itemized
→ A

**G4. Itemized contributions storage (large)?**
a) Aggregate at build, store summaries; raw in R2/static ⭐  b) Full itemized in DB  c) Skip itemized
→ A

**G5. PAC / outside spending?**
a) Independent expenditures by committee, V1 ⭐  b) Defer  c) Candidate committees only
→ A

**G6. "Dark money" / 501(c)(4)?**
a) Note limitation, link OpenSecrets ⭐  b) Attempt estimate  c) Skip
→ A

**G7. Money-flow visualization?**
a) Sankey/flow + bar comparisons ⭐  b) Tables only  c) Bars only
→ A

**G8. Donor geography?**
a) In-state vs out-of-state split ⭐  b) By ZIP map (heavy)  c) Skip
→ A

**G9. Small-dollar vs large-dollar?**
a) % under $200 metric ⭐  b) Full distribution  c) Skip
→ A

**G10. Self-funding flag?**
a) Yes, candidate loans/contributions ⭐  b) Skip
→ A

**G11. Cross-cycle finance history?**
a) Current cycle + prior for incumbents ⭐  b) Current only  c) All available
→ A

**G12. Committee↔candidate linking?**
a) Use FEC linkages (principal campaign cmte) ⭐  b) Manual  c) Skip
→ A

**G13. Finance freshness display?**
a) "Through <coverage_end_date>" per filing ⭐  b) Fetch date  c) None
→ A

**G14. Finance data licensing note?**
a) FEC public domain, OpenSecrets attribution ⭐  b) Skip attribution  c) Lawyer it
→ A

---

## H · Polling estimation / aggregation (H1–H14)

**H1. Poll data source?**
a) 538 polls CSV + Wikipedia race tables + scrape RCP ⭐  b) Single source  c) Manual entry  d) Paid
→ A

**H2. Aggregation method V1?**
a) Weighted trailing average (recency + sample + pollster rating) ⭐  b) Simple average  c) Bayesian state-space (later) ⭐ if time
→ A + C

**H3. Pollster quality weighting?**
a) Use 538 pollster ratings where available ⭐  b) Equal weight  c) Our own rating
→ A for now, but C later on.

**H4. House-effects / bias adjustment?**
a) Light pollster-lean adjustment, documented ⭐  b) None  c) Full (later)
→ A

**H5. Polling display?**
a) Trend line + dots + average band ⭐  b) Latest only  c) Table
→ A

**H6. Sparse-polling races (most House)?**
a) Fall back to fundamentals + rating, label "no recent polls" ⭐  b) Hide polling  c) National generic-ballot proxy ⭐
→ A

**H7. Generic congressional ballot?**
a) Track + use as House prior ⭐  b) Display only  c) Skip
→ A

**H8. Uncertainty representation?**
a) Show margin of error + band always ⭐  b) Point estimate  c) Both
→ A

**H9. Poll recency decay?**
a) Exponential decay weighting ⭐  b) Hard cutoff window  c) None
→ A

**H10. Partisan-sponsored polls?**
a) Include, flagged + down-weighted ⭐  b) Exclude  c) Include unflagged
→ A

**H11. Aggregation compute home?**
a) Python in GitHub Action, output static JSON ⭐  b) In-browser  c) Serverless function
→ A

**H12. Polling methodology page?**
a) Yes, full transparency ⭐  b) Short note  c) None
→ A

**H13. Cross-validate aggregate vs result (post-election)?**
a) Yes, public accuracy scorecard ⭐  b) Internal only  c) Skip
→ A

**H14. Poll provenance?**
a) Each poll → pollster, dates, n, source link ⭐  b) Source page  c) Trust feed
→ A

---

## I · Demographic analytics (I1–I14)

**I1. Demographic source?**
a) US Census ACS via Census API (free key) ⭐  b) Census bulk  c) Third-party
→ A

**I2. Geographic grain?**
a) Congressional district + state ⭐  b) County  c) Tract (heavy)
→ A

**I3. Census→district mapping?**
a) Census 119th-Congress district equivalency + TIGER shapes ⭐  b) Approximate  c) Skip district-level
→ A

**I4. Demographic variables V1?**
a) Age, race/ethnicity, income, education, urbanicity ⭐  b) Just race + income  c) Full ACS table set
→ A

**I5. Time series?**
a) Latest ACS 5-yr + one prior ⭐  b) Latest only  c) Decennial + ACS
→ A

**I6. Display?**
a) District profile card + comparison-to-national ⭐  b) Maps  c) Tables
→ A

**I7. Storage (Census is big)?**
a) Pre-aggregate per district at build → static JSON ⭐  b) Query DB live  c) Census API live (rate limits)
→ A

**I8. Cross-link demo ↔ race ↔ result?**
a) Yes (district demo on race page) ⭐  b) Separate module  c) Later
→ A

**I9. ACS margin-of-error handling?**
a) Carry + display MOE on estimates ⭐  b) Ignore  c) Footnote
→ A

**I10. Citizen Voting Age Population (CVAP)?**
a) Include for enfranchisement context ⭐  b) Total pop only  c) Skip
→ A

**I11. Urban/rural classification?**
a) Census urbanized-area based ⭐  b) Custom  c) Skip
→ A

**I12. Redistricting-aware (2022 maps)?**
a) Use current (post-2020) district lines ⭐  b) Old lines  c) Both
→ There are 2026 redistricting maps that need to be aware

**I13. Comparison framing?**
a) District vs state vs national ⭐  b) District only  c) Rank among all districts
→ A

**I14. Demographic data caveats page?**
a) Yes (ACS limits, ecological fallacy warning) ⭐  b) Footnotes  c) None
→ A

---

## J · Issue & party-demographic analytics (J1–J10) — mostly later

**J1. Issue-salience data source?**
a) Gallup/Pew published toplines, cited (deferred to v1.x) ⭐  b) Scrape polls  c) Skip entirely
→ A

**J2. Issue analytics V1 depth?**
a) Defer — stub + "coming soon" ⭐  b) Light national issue tracker  c) Full
→ A

**J3. Party-demographic crosstabs source?**
a) Exit polls + Pew typology, cited (later) ⭐  b) Derive from our demo+result  c) Skip
→ A

**J4. Ecological-inference risk (party-by-demo)?**
a) Avoid individual inference; show aggregate correlations + caveat ⭐  b) Model it  c) Skip
→ A

**J5. Issue↔race linking?**
a) Later  b) Tag races by salient issue  c) Skip ⭐
→ A

**J6. Sentiment/news analysis?**
a) Out of scope V1 ⭐  b) Light headline tracker  c) Full NLP
→ A for now, B/C later on

**J7. Where issue analytics sits in roadmap?**
a) v1.x after core data modules ⭐  b) V1  c) v2
→ A

**J8. Party realignment / trend module?**
a) Later — historical swing maps ⭐  b) V1  c) Skip
→ A

**J9. Data-quality bar for issue claims?**
a) Only published, named-source toplines ⭐  b) Aggregate freely  c) Our estimates
→ A

**J10. Stub now to reserve URL/SEO?**
a) Yes, indexable placeholder ⭐  b) No
→ A

---

## K · Party / caucus / chamber composition (K1–K12)

**K1. Chamber composition source?**
a) Congress.gov API + Clerk/Senate official ⭐  b) Wikipedia  c) ProPublica (deprecated — avoid)
→ A

**K2. Caucus/membership data?**
a) Official + unitedstates/congress-legislators YAML (free, maintained) ⭐  b) Manual  c) Skip
→ A

**K3. Live seat math display?**
a) Current balance + "if election held" projected balance ⭐  b) Current only  c) Projected only
→ A

**K4. Caucus groupings (Freedom, Progressive, etc.)?**
a) Major caucuses, sourced membership ⭐  b) Party only  c) Skip
→ A

**K5. Majority-control tracker?**
a) Seats-to-flip + tipping-point race ⭐  b) Simple count  c) Skip
→ A

**K6. Committee assignments?**
a) Include (Congress.gov) ⭐  b) Leadership only  c) Skip
→ A

**K7. Leadership tracking?**
a) Yes (Speaker, Leaders, Whips) ⭐  b) Skip
→ A

**K8. Independents/caucusing-with?**
a) Model "caucuses with D/R" explicitly ⭐  b) Count as party  c) Separate
→ A

**K9. Historical chamber control?**
a) Timeline since e.g. 2000 ⭐  b) Current only  c) Skip
→ A

**K10. Vacancy tracking?**
a) Yes, affects seat math ⭐  b) Skip
→ A

**K11. Update cadence?**
a) Weekly + on known events ⭐  b) Nightly  c) Manual
→ A

**K12. Senate class / up-for-election logic?**
a) Compute Class II (2026) automatically ⭐  b) Hard-code  c) Skip
→ A

---

## L · Gerrymandering / redistricting (L1–L14)

**L1. District geometry source?**
a) Census TIGER/Line shapefiles (current districts) ⭐  b) Redistricting Data Hub  c) Dave's Redistricting exports
→ A

**L2. Compactness metrics V1?**
a) Polsby-Popper + Reock + convex-hull ⭐  b) Polsby-Popper only  c) Visual only, no metric
→ A

**L3. Partisan-fairness metrics?**
a) Efficiency gap + mean-median (with caveats) ⭐  b) Efficiency gap only  c) Skip metrics
→ A

**L4. Map rendering tech?**
a) MapLibre GL + PMTiles (static, free) ⭐  b) Leaflet + GeoJSON  c) D3 topojson  d) Static images
→ A

**L5. Tile generation?**
a) tippecanoe → PMTiles in CI, served from R2/static ⭐  b) GeoJSON direct (small only)  c) Vector tile service
→ A

**L6. Geo compute (metrics)?**
a) Python GeoPandas/Shapely in Action → static JSON ⭐  b) PostGIS queries  c) Turf.js client-side
→ A

**L7. Do we need PostGIS at all?**
a) No — precompute metrics offline, PostGIS optional ⭐  b) Yes, Postgres+PostGIS  c) Decide in O-section
→ A

**L8. Gerrymander "score" framing?**
a) Multi-metric + "metrics disagree" caveat, no single verdict ⭐  b) Single composite score  c) Raw metrics only
→ A

**L9. Historical map comparison?**
a) Pre/post-2020 redistricting where notable ⭐  b) Current only  c) Skip
→ A

**L10. Court-ordered map changes (ongoing)?**
a) Track per-state status, sourced ⭐  b) Snapshot  c) Skip
→ A

**L11. Ensemble/simulation analysis (advanced)?**
a) Later — note method, link academic tools ⭐  b) V1 lite ensemble  c) Skip
→ A

**L12. District comparison UI?**
a) "Most/least compact" leaderboard + map ⭐  b) Per-district only  c) Map only
→ A

**L13. State legislature gerrymandering?**
a) Later (federal districts first) ⭐  b) V1  c) Skip
→ A

**L14. Methodology transparency?**
a) Full formulas + limitations page ⭐  b) Short note  c) None
→ A

---

## M · Congressional member analytics (M1–M12)

**M1. Member roster source?**
a) unitedstates/congress-legislators (YAML, bioguide ids) ⭐  b) Congress.gov API  c) Both ⭐
→ C

**M2. Voting record source?**
a) Congress.gov roll-call + GovTrack ⭐  b) Voteview (DW-NOMINATE)  c) Both ⭐
→ C

**M3. Ideology score?**
a) Voteview DW-NOMINATE (academic, free) ⭐  b) Our own  c) Skip
→ A

**M4. Member profile contents V1?**
a) Bio, district, committees, key votes, finance, ideology ⭐  b) Bio + votes  c) Configurable
→ A

**M5. Bill sponsorship?**
a) Sponsored/cosponsored counts + notable ⭐  b) Skip  c) Full
→ A

**M6. Attendance / missed votes?**
a) Include (from roll calls) ⭐  b) Skip
→ A

**M7. Bipartisanship metric?**
a) Cross-party cosponsorship index ⭐  b) Skip  c) Later
→ A

**M8. Member ↔ race ↔ finance linking?**
a) Full cross-link ⭐  b) Profile siloed  c) Later
→ A

**M9. Photos?**
a) unitedstates/images (public) ⭐  b) Wikipedia  c) None
→ A

**M10. Senators + Representatives?**
a) Both (all 535) ⭐  b) House only  c) Up-for-election only
→ A

**M11. Update cadence?**
a) Weekly + on new roll calls ⭐  b) Nightly  c) Per-session
→ A

**M12. Statements/news?**
a) Out of scope V1 ⭐  b) Press-release feed  c) Full
→ A for now, but maybe B/C in the future

---

## N · Election modeling / forecast (N1–N16) — the signature module

**N1. Forecast philosophy?**
a) Transparent + heuristic-first, ML only if it beats it ⭐  b) Full Bayesian from day 1  c) Pure poll average
→ A for now with potential to include B later

**N2. Model inputs V1?**
a) Polls + fundamentals (finance, incumbency, partisanship, ratings) ⭐  b) Polls only  c) Fundamentals only
→ A

**N3. Partisan baseline?**
a) Prior presidential/CPVI-style lean per district ⭐  b) Last result  c) None
→ A

**N4. Output type?**
a) Win probability + predicted margin + range, per race ⭐  b) Rating bucket only  c) Margin only
→ A

**N5. Chamber forecast?**
a) Monte Carlo sim → seat distribution + control prob ⭐  b) Sum of point estimates  c) Skip chamber-level
→ A

**N6. Correlated error in sim?**
a) Yes — national swing correlation across races ⭐  b) Independent races (simpler)  c) Later
→ A

**N7. Implementation?**
a) Python (numpy/pandas/scikit) in CI → static forecast JSON ⭐  b) In-browser JS  c) Notebook only
→ A
 
**N8. ML element (for skill-showcase)?**
a) Add a documented model (e.g. ridge/GBM on fundamentals) compared to heuristic ⭐  b) None  c) Heavy ML
→ A

**N9. Uncertainty calibration?**
a) Backtest on 2018/2022 + show calibration ⭐  b) Assume  c) Skip
→ A

**N10. Update cadence?**
a) Nightly rebuild ⭐  b) Weekly  c) On new polls
→ A

**N11. Forecast history?**
a) Store daily snapshots → "forecast over time" chart ⭐  b) Latest only  c) Skip
→ A

**N12. Transparency?**
a) Open methodology + inputs downloadable ⭐  b) Methodology page  c) Black box
→ A

**N13. Reproducibility?**
a) Seeded sims + versioned model + tests ⭐  b) Best-effort  c) Skip
→ A

**N14. Senate vs House model difference?**
a) Senate poll-heavy, House fundamentals-heavy ⭐  b) Same model both  c) Senate only
→ A

**N15. Governor/other forecasts?**
a) Key governors, same engine ⭐  b) Skip  c) All statewide
→ A

**N16. Post-election accuracy report?**
a) Public scorecard vs actual ⭐  b) Internal  c) Skip
→ A

---

## O · Data architecture & storage (no-Supabase) (O1–O18)

**O1. Core storage philosophy?**
a) Bake slow data static at build (git-as-data) + small DB only where needed ⭐  b) DB-centric  c) All static
→ A

**O2. Primary database (if any)?**
a) Neon (serverless Postgres, free) ⭐  b) Turso (libSQL/SQLite, free)  c) Cloudflare D1 (SQLite)  d) None — static only
→ A with potential B on the side. We'll need better storage since Neon only has 0.5 on free version.

**O3. Why that DB? (confirm trade-off)**
a) Postgres = hireable + SQL + optional PostGIS ⭐  b) SQLite/D1 = simplest + edge  c) Reconsider
→ A

**O4. Large blobs (tiles, bulk CSV, raw filings)?**
a) Cloudflare R2 (free egress) ⭐  b) GitHub LFS  c) Commit small, gitignore large + refetch  d) R2 + C ⭐
→ D

**O5. Hot key-value / caching?**
a) Cloudflare KV or Upstash Redis (free) if needed ⭐  b) None V1  c) In-memory only
→ A

**O6. Where does most read traffic hit?**
a) Static JSON/HTML on CDN (no DB on hot path) ⭐  b) DB queries  c) API routes
→ A

**O7. Data format for baked outputs?**
a) JSON + Parquet for downloads ⭐  b) JSON only  c) SQLite file shipped to client
→ A

**O8. Schema management?**
a) Drizzle ORM + migrations (TS, hireable) ⭐  b) Prisma  c) Raw SQL  d) Kysely
→ A

**O9. Do we need the DB for V1 at all, honestly?**
a) Minimal — forecast snapshots, feed items, maybe search ⭐  b) Heavily  c) Not at all V1
→ A

**O10. Free-tier limit we measure first?**
a) Actions minutes + API quotas + bandwidth (storage is fine) ⭐  b) DB rows  c) Don't measure
→ A

**O11. Data versioning/provenance?**
a) `as_of` + `source_hash` on every dataset + DATA_SOURCES.md ⭐  b) Git history  c) None
→ A

**O12. Bronze/silver/gold layering (metrotrack-style)?**
a) Yes — raw → cleaned → published ⭐  b) Two layers  c) Single transform
→ A

**O13. Backups?**
a) Git is the backup for static; DB snapshot to R2 weekly ⭐  b) DB provider snapshots  c) None V1
→ A

**O14. Search?**
a) Static client-side index (Pagefind) ⭐  b) DB full-text  c) Algolia free  d) None V1
→ A (We need to study Google's use of bloom filters and other search methods that are extremely efficent)

**O15. API for our own data (dogfood + portfolio)?**
a) Static JSON endpoints + documented ⭐  b) Real REST/tRPC API  c) None V1
→ A

**O16. Multi-cycle data layout?**
a) Partition by `cycle` (2026, 2028…) from day 1 ⭐  b) 2026 flat, refactor later  c) Single table
→ A

**O17. PostGIS or offline geo?**
a) Offline (GeoPandas in CI), no PostGIS ⭐  b) PostGIS in Neon  c) Decide per-need
→ A

**O18. Secret/connection management?**
a) GitHub Actions secrets + Vercel/CF env, never committed ⭐  b) .env only  c) Vault
→ A

---

## P · Frontend framework & stack (P1–P14)

**P1. Framework?**
a) Astro (content+SEO+islands) — diversifies from your Next.js work ⭐  b) Next.js (App Router) — most hireable  c) SvelteKit  d) Remix
→ A

**P2. Rationale check?**
a) Astro = best for content/SEO/data-viz + React islands keeps React skill ⭐  b) Next = one framework, RSC skill  c) Reconsider
→ A

**P3. Interactive islands library?**
a) React (keep hireable React skill in Astro) ⭐  b) Svelte  c) Vue  d) Preact (lighter)
→ A

**P4. Language?**
a) TypeScript strict everywhere ⭐  b) TS loose  c) JS
→ A

**P5. Rendering strategy?**
a) Static SSG + islands; ISR/on-demand only for live results ⭐  b) Mostly SSR  c) SPA
→ A

**P6. Hosting?**
a) Cloudflare Pages (free, generous) ⭐  b) Vercel (best Next DX)  c) Netlify  d) GitHub Pages
→ A

**P7. Charts library?**
a) Observable Plot (fast, elegant) + D3 for custom ⭐  b) Recharts  c) visx  d) Chart.js
→ A

**P8. Maps library?**
a) MapLibre GL + PMTiles ⭐  b) Leaflet  c) D3-geo
→ A

**P9. Data fetching (client)?**
a) Mostly none — static JSON; TanStack Query for live bits ⭐  b) SWR  c) Native fetch
→ A

**P10. Forms/inputs (find-your-district)?**
a) Native + minimal JS ⭐  b) React Hook Form  c) Heavy lib
→ A

**P11. Content/articles authoring?**
a) MDX in repo ⭐  b) Headless CMS (free tier)  c) Markdown + frontmatter
→ A

**P12. Monorepo?**
a) Single repo, pnpm workspaces if needed (pipeline + web) ⭐  b) Two repos  c) Turborepo
→ A

**P13. Package manager?**
a) pnpm ⭐  b) npm  c) bun (also build speed)
→ A

**P14. Component testing/dev?**
a) Vitest + Playwright; Storybook deferred ⭐  b) Jest  c) None V1
→ A

---

## Q · Mapping & geospatial (Q1–Q10)

**Q1. Base map style?**
a) Minimal custom (no Mapbox token) ⭐  b) Carto free tiles  c) OSM raster
→ A

**Q2. District boundaries delivery?**
a) PMTiles vector ⭐  b) Simplified GeoJSON  c) TopoJSON
→ A

**Q3. Geometry simplification?**
a) Pre-simplify per zoom (mapshaper/tippecanoe) ⭐  b) Full-res  c) One simplified level
→ A

**Q4. Choropleth metrics on map?**
a) Margin, demo, compactness toggleable ⭐  b) Margin only  c) No choropleth
→ A

**Q5. Address→district lookup?**
a) Census Geocoder API (free) ⭐  b) Client point-in-polygon  c) Google (paid)
→ A

**Q6. Map performance budget?**
a) Tiles + viewport culling, ≤ a few MB ⭐  b) Best-effort  c) Ignore
→ A

**Q7. Mobile map UX?**
a) Simplified + list fallback ⭐  b) Same as desktop  c) Static image on mobile
→ A

**Q8. Accessibility of maps?**
a) Data table equivalent + ARIA ⭐  b) Alt text  c) None
→ A

**Q9. State vs district zoom levels?**
a) National → state → district ⭐  b) District only  c) State only
→ A

**Q10. Tile hosting?**
a) R2/static, single PMTiles per layer per cycle ⭐  b) Per-state files  c) Tile server
→ A

---

## R · ETL / pipeline / freshness (R1–R14)

**R1. Pipeline language?**
a) Python (pandas/geopandas/requests) — data skill ⭐  b) TypeScript  c) Mix (TS web, Py data) ⭐
→ C

**R2. Orchestration?**
a) GitHub Actions cron per source ⭐  b) A workflow engine (Airflow — overkill)  c) Manual scripts
→ A

**R3. Per-source cadence?**
a) Independent schedules (finance weekly, polls daily, etc.) ⭐  b) One nightly job  c) Manual
→ A

**R4. Idempotency?**
a) Upsert by natural key, no truncate; re-runnable ⭐  b) Rebuild from scratch  c) Append
→ A

**R5. Freshness floors?**
a) Per-source max-age check → alert if stale ⭐  b) None  c) Display only
→ A

**R6. Smoke test before publish?**
a) `--dry-run` validates sources+schema first ⭐  b) None  c) Post-hoc
→ A

**R7. Schema validation?**
a) Pydantic/zod on every ingested record ⭐  b) Loose  c) None
→ A

**R8. Failure handling?**
a) Fail the source, keep last-good, open issue ⭐  b) Hard fail all  c) Silent
→ A

**R9. Data tests?**
a) Range/null/row-count assertions (dbt-style or custom) ⭐  b) Spot checks  c) None
→ A

**R10. Caching upstream calls?**
a) Cache + conditional requests to respect quotas ⭐  b) Always refetch  c) None
→ A

**R11. Pipeline output target?**
a) Commit static JSON/Parquet + push to R2 ⭐  b) Write to DB  c) Both ⭐
→ A

**R12. Reproducible env?**
a) Pinned requirements + uv/poetry lock ⭐  b) Loose  c) Docker
→ A

**R13. Backfill strategy?**
a) Parameterized `--cycle --since` ⭐  b) Manual  c) None
→ A

**R14. DATA_SOURCES.md as contract?**
a) Yes — every figure maps to a row (source, url, license, cadence) ⭐  b) Informal  c) None
→ A

---

## S · Autonomous loops, Actions, QA, self-emailed issues (S1–S18)

**S1. Build-loop driver?**
a) ralph-loop + `LOOP_PROMPT.md` + `PROGRESS.md` ledger (metrotrack pattern) ⭐  b) Manual phases  c) Plain Actions
→ A

**S2. Loop unit of work?**
a) A race/state/module config = one unit ⭐  b) A phase  c) A PR
→ A

**S3. Orchestrator vs worker?**
a) Orchestrator picks unit → spawns cold sub-agent → gates → PR ⭐  b) One agent does all  c) No agents
→ A

**S4. Hard verification gate?**
a) build+tests+a11y+Lighthouse≥90+data-integrity, re-run by orchestrator ⭐  b) build only  c) Trust worker
→ A

**S5. `main` protection?**
a) Loop never touches main; merges to `dev`, human approves main ⭐  b) Loop merges main  c) No protection
→ A

**S6. Budget check before spawn?**
a) Yes — Actions minutes + API quota + bandwidth ⭐  b) No  c) Monthly review
→ A

**S7. Nightly autonomous QA?**
a) Scheduled Action runs gate vs live site, opens issue on regression ⭐  b) Manual QA  c) None
→ A

**S8. QA tooling?**
a) Playwright + Lighthouse CI + link/schema checks ⭐  b) Lighthouse only  c) Manual
→ A

**S9. Self-emailed issues (item 4, metrotrack-style)?**
a) Action → Resend API → your inbox on failure/regression ⭐  b) GitHub notif only  c) SMTP via Gmail app-password  d) A+B ⭐
→ C

**S10. Email contents?**
a) Summary + diff + run link + severity ⭐  b) Just "failed"  c) Full logs
→ A

**S11. Issue auto-filing?**
a) Open/Update GitHub issue + label, dedupe by signature ⭐  b) New issue each time  c) None
→ A

**S12. Loop guardrails?**
a) Auto: read/build/test/git on non-main; gated: deploy + main ⭐  b) Full auto  c) Manual approve each step
→ B

**S13. Concurrency?**
a) ≤2–3 worktrees live (respect limits) ⭐  b) Unbounded  c) Serial only
→ A

**S14. Evidence requirement?**
a) Every unit PR has screenshots + Lighthouse + integrity log ⭐  b) Description only  c) None
→ A

**S15. Data-pipeline QA in loop?**
a) Validate freshness + source rows + schema each run ⭐  b) Build only  c) None
→ A

**S16. Stop conditions?**
a) No eligible unit / budget wall / human pause, then report ⭐  b) Run forever  c) Fixed count
→ A

**S17. Where loop state lives?**
a) `PROGRESS.md` ledger + activity log ⭐  b) GitHub Projects  c) Issues
→ A

**S18. Scheduled cloud agents (Claude routines) vs Actions?**
a) Actions for CI/data; Claude routine for higher-level weekly review ⭐  b) Only Actions  c) Only routines
→ A

---

## T · Email, accounts, secrets, free-tier survival (T1–T12) — solves "out of emails"

**T1. The email-exhaustion fix (primary)?**
a) Custom domain + Cloudflare Email Routing → unlimited aliases → one inbox ⭐  b) Gmail `+alias` addressing  c) New Gmail accounts  d) A+B ⭐
→ D

**T2. Why A? (confirm)**
a) `fec@an9.dev`, `neon@an9.dev`… all land in one inbox, free, unlimited ⭐  b) `+` works but some sites block it ⭐note  c) Reconsider
→ A + B

**T3. Catch-all routing?**
a) Catch-all → one inbox, per-service alias on signup ⭐  b) Explicit aliases only  c) No catch-all (spam)
→ A

**T4. Outbound email (alerts/digests)?**
a) Resend (free 3k/mo, custom domain) ⭐  b) Gmail SMTP app-password  c) SendGrid free
→ B

**T5. Which services actually need a new account?**
a) Minimize — Neon, Cloudflare, Resend, Vercel/CF only ⭐  b) Many  c) Reuse existing where possible ⭐
→ A/C

**T6. API keys needed (free)?**
a) api.data.gov (FEC+Census+Congress share it), 538 (no key), Voteview (no key) ⭐  b) List per source  c) Avoid keyed APIs
→ A

**T7. Secret storage?**
a) GitHub Actions secrets + host env vars ⭐  b) .env (gitignored)  c) Manager
→ A

**T8. Rate-limit strategy?**
a) Cache + backoff + stagger across nights ⭐  b) Hope  c) Paid tier
→ A

**T9. Budget alarms?**
a) Track Actions minutes + quotas, alert at 80% ⭐  b) None  c) Monthly check
→ A

**T10. Account inventory doc?**
a) `docs/ACCOUNTS.md` (service, alias used, free limits) — gitignored if sensitive ⭐  b) Memory  c) Password manager only
→ A

**T11. Domain cost (only non-free item)?**
a) ~$10/yr domain is worth it for aliases+brand+email ⭐  b) Use free subdomain, `+alias` for email  c) Skip domain
→ A

**T12. 2FA/security on these accounts?**
a) Authenticator app on all ⭐  b) SMS  c) None
→ A

---

## U · SEO (U1–U14)

**U1. SEO priority?**
a) High, built-in from phase 1 ⭐  b) Add later  c) Low
→ A

**U2. Per-page meta?**
a) Templated titles/descriptions with live figures ⭐  b) Static  c) Default
→ A

**U3. Structured data?**
a) JSON-LD: Dataset + Organization + BreadcrumbList + Article ⭐  b) Organization only  c) None
→ A

**U4. Sitemap?**
a) Auto-generated `sitemap.xml` ⭐  b) Manual  c) None
→ A

**U5. OG/Twitter images?**
a) Per-page generated at build ⭐  b) One default  c) None
→ A

**U6. URL scheme?**
a) Clean kebab: `/2026/senate/ohio`, `/members/<bioguide>` ⭐  b) Query params  c) IDs
→ A

**U7. Canonicals?**
a) Self-canonical + handle dupes ⭐  b) None  c) Later
→ A

**U8. Core Web Vitals target?**
a) Lighthouse ≥90 mobile in CI (gate) ⭐  b) Best-effort  c) Ignore
→ A

**U9. Content for search intent?**
a) Race/district pages answer "who's running in X" ⭐  b) Data only  c) Articles only
→ A

**U10. Internal linking?**
a) Dense cross-links (race↔member↔district↔money) ⭐  b) Nav only  c) Minimal
→ A

**U11. Freshness signals?**
a) "Updated <date>" + lastmod in sitemap ⭐  b) None  c) Manual
→ A

**U12. robots/crawl?**
a) Open, with sane crawl + no thin pages indexed ⭐  b) Open all  c) Restrict
→ A

**U13. Analytics (privacy)?**
a) Plausible/Umami self-host or free ⭐  b) GA4  c) None
→ A

**U14. RSS/feeds for discovery?**
a) Per-cycle + per-module feeds (metrotrack pattern) ⭐  b) One global  c) None V1
→ A

---

## V · Security (V1–V12)

**V1. Threat model focus (mostly static, no PII)?**
a) Supply-chain + secrets + integrity, not user-data ⭐  b) Full app sec  c) Minimal
→ A

**V2. Secrets in CI?**
a) Never logged, scoped, rotated ⭐  b) Basic  c) Ignore
→ A

**V3. Dependency security?**
a) Dependabot + `npm audit`/`pip-audit` in CI ⭐  b) Manual  c) None
→ A

**V4. Supply-chain pinning?**
a) Lockfiles + pinned Action SHAs ⭐  b) Tags  c) Latest
→ A

**V5. Headers?**
a) CSP + HSTS + X-Frame-Options + referrer-policy ⭐  b) Defaults  c) None
→ A

**V6. Input handling (district lookup, search)?**
a) Validate/sanitize, no eval, static where possible ⭐  b) Trust  c) N/A
→ A

**V7. API routes (if any)?**
a) Rate-limit + input validation + no secrets client-side ⭐  b) Basic  c) None
→ A

**V8. Data integrity / tamper?**
a) `source_hash` + reproducible builds ⭐  b) Trust  c) None
→ A

**V9. Forecast manipulation resistance?**
a) Versioned, seeded, auditable model ⭐  b) None
→ A

**V10. Branch protection?**
a) Required checks + no force-push to main ⭐  b) Basic  c) None
→ A

**V11. Security review cadence?**
a) `/security-review` per phase + pre-launch ⭐  b) Once  c) None
→ A

**V12. Disclosure/contact?**
a) `SECURITY.md` + alias email ⭐  b) None
→ A

---

## W · Accessibility (W1–W10)

**W1. Target?**
a) WCAG 2.2 AA ⭐  b) A  c) Best-effort
→ A

**W2. Charts a11y?**
a) Data-table equivalent + ARIA + text summary ⭐  b) Alt text  c) None
→ A

**W3. Color independence?**
a) Never color-only; patterns/labels for party ⭐  b) Color + legend  c) Color only
→ A

**W4. Keyboard nav?**
a) Full keyboard + visible focus ⭐  b) Partial  c) None
→ A

**W5. Reduced motion?**
a) Respect `prefers-reduced-motion` ⭐  b) Ignore
→ A

**W6. Screen-reader testing?**
a) In QA checklist ⭐  b) Ad-hoc  c) None
→ A

**W7. Contrast?**
a) AA ratios enforced in tokens ⭐  b) Eyeball  c) Ignore
→ A

**W8. Maps a11y fallback?**
a) Accessible table/list of same data ⭐  b) Alt text  c) None
→ A

**W9. Automated a11y checks?**
a) axe in Playwright CI ⭐  b) Manual  c) None
→ A

**W10. Forms/labels?**
a) Proper labels + error messaging ⭐  b) Placeholder-only  c) N/A
→ A

---

## X · Performance & device optimization (X1–X10)

**X1. Budget?**
a) Hard JS/image budgets per route, enforced in CI ⭐  b) Soft  c) None
→ A

**X2. Hydration?**
a) Islands — ship minimal JS, static by default ⭐  b) Full hydration  c) SPA
→ A

**X3. Images?**
a) Modern formats + responsive + lazy (Astro Image) ⭐  b) Manual  c) Raw
→ A

**X4. Fonts?**
a) Self-host + subset + `font-display:swap` ⭐  b) Google Fonts CDN  c) System
→ A

**X5. Data payloads?**
a) Per-page minimal JSON, split by route ⭐  b) One big bundle  c) Live fetch
→ A

**X6. Caching?**
a) Immutable hashed assets + CDN + stale-while-revalidate ⭐  b) Default  c) None
→ A

**X7. Local-device optimization (low-end mobile)?**
a) Test on throttled CPU/network in CI ⭐  b) Desktop only  c) Ignore
→ A

**X8. Map/chart laziness?**
a) Defer/lazy heavy islands until in view ⭐  b) Eager  c) N/A
→ A

**X9. Offline/PWA?**
a) Later — maybe basic offline for saved district ⭐  b) Full PWA V1  c) Never
→ A

**X10. Perf monitoring?**
a) Lighthouse CI trend + budget alerts ⭐  b) Manual  c) None
→ A

---

## Y · Content / articles / regular updates (Y1–Y14)

**Y1. Articles in V1?**
a) Yes — MDX, launch with a few ⭐  b) Stub the section  c) Later
→ A

**Y2. Content cadence?**
a) Weekly data-recap + ad-hoc deep dives ⭐  b) Daily  c) Irregular
→ A

**Y3. Auto-generated update posts?**
a) "What changed this week" drafted from data diffs, human-reviewed ⭐  b) Fully manual  c) Fully auto
→ A

**Y4. Article types?**
a) Data recaps + explainers + methodology ⭐  b) Recaps only  c) Opinion (labeled)
→ A

**Y5. Bylines?**
a) Single author (you) + "data" byline for autogen ⭐  b) Anonymous  c) Multiple
→ A

**Y6. Article SEO?**
a) Full (JSON-LD Article, OG, internal links) ⭐  b) Basic  c) None
→ A

**Y7. Newsletter?**
a) Later — collect interest, send via Resend ⭐  b) V1  c) Never
→ A

**Y8. Embed live data in articles?**
a) Yes — MDX components pull current figures ⭐  b) Static snapshots  c) Text only
→ A

**Y9. Content review before publish?**
a) Human approves any autogen claim ⭐  b) Spot-check  c) Auto-publish
→ A

**Y10. Archive/tagging?**
a) Tags + cycle + topic ⭐  b) Date only  c) Flat
→ A

**Y11. Comments on articles?**
a) None V1 ⭐  b) Reactions  c) Comments
→ A

**Y12. Social distribution?**
a) Auto-draft posts for review (not auto-post) ⭐  b) Auto-post  c) None
→ A

**Y13. Citation style in articles?**
a) Inline links + sources block ⭐  b) Footnotes  c) None
→ A

**Y14. Election-night liveblog?**
a) Lightweight, later ⭐  b) V1 ambition  c) Skip
→ A

---

## Z · Claude tooling, agents, token efficiency (Z1–Z12)

**Z1. Plugin set to standardize on?**
a) serena + ralph-loop + rtk + caveman + ponytail + superpowers + compound-engineering ⭐  b) Subset  c) Decide later
→ A

**Z2. serena role?**
a) Symbol-level code nav (cheaper than reading files) ⭐  b) Skip  c) Light
→ A

**Z3. ralph-loop role?**
a) Drive the autonomous build/rollout loop ⭐  b) Skip  c) Light
→ A

**Z4. rtk role?**
a) Token-optimized CLI proxy on all dev ops ⭐  b) Skip
→ A

**Z5. caveman/ponytail?**
a) Keep on — terse output + lazy/minimal builds ⭐  b) Off  c) caveman only
→ A

**Z6. Agent token strategy?**
a) Cold sub-agents driven by plan files, not chat context ⭐  b) One long session  c) Mix
→ A

**Z7. Which model for which job?**
a) Opus for planning/gating, Haiku/Sonnet for mechanical sub-agents ⭐  b) Opus everywhere  c) One model
→ A

**Z8. Specialized agents to lean on?**
a) Explore (search), cavecrew-investigator (locate), ce-* reviewers ⭐  b) general-purpose only  c) None
→ A

**Z9. Context7 / docs?**
a) Use for library docs (Astro, Drizzle, MapLibre) on demand ⭐  b) Web search  c) Memory
→ A

**Z10. Memory/knowledge capture?**
a) Per-phase MEMORY.md + DECISIONS + this questionnaire's `[id]` chain ⭐  b) Git only  c) None
→ A

**Z11. graphify / codebase Q&A?**
a) Build a knowledge graph once repo is sizable ⭐  b) Skip  c) Later
→ A

**Z12. Cloud vs local agents?**
a) Local loops + scheduled cloud routine for weekly review ⭐  b) All local  c) All cloud
→ A

---

## ZZ · Versioning, workflow, legal/ethics (ZZ1–ZZ10)

**ZZ1. Versioning scheme?**
a) `v[phase].[segment].[task]` (metrotrack) ⭐  b) SemVer features  c) Date-based
→ A

**ZZ2. Branch/workflow ritual?**
a) Phase branch → segment sub-branches → WORKFLOW ritual + DoD ⭐  b) Trunk-based  c) Ad-hoc
→ A

**ZZ3. Definition of Done?**
a) Shared `DEFINITION_OF_DONE.md` (sourced+tested+a11y+perf+SEO) ⭐  b) Per-task  c) Informal
→ A

**ZZ4. ADRs?**
a) Yes for non-obvious calls (DB, framework, model) ⭐  b) DECISIONS.md only  c) None
→ A

**ZZ5. Phase-0 bootstrap (ACOS pattern)?**
a) Docs + schema + contracts before business logic ⭐  b) Code-first  c) Mix
→ A

**ZZ6. Data licensing compliance?**
a) Per-source license noted in DATA_SOURCES.md; attribute where required ⭐  b) Assume public  c) Lawyer
→ A

**ZZ7. Polling/forecast ethical guardrails?**
a) Disclaimers + uncertainty + no voter-suppression framing ⭐  b) Disclaimer only  c) None
→ A

**ZZ8. Election-integrity stance?**
a) Mirror official sources, never originate calls/claims ⭐  b) Our calls  c) N/A
→ A

**ZZ9. Privacy?**
a) No accounts, privacy-analytics, no PII stored ⭐  b) Minimal accounts  c) Full analytics
→ A

**ZZ10. License for the repo/code?**
a) MIT code + data under source licenses, content CC-BY ⭐  b) All-rights-reserved  c) Decide later
→ A

---

### After you answer

Survivors graduate into `docs/phases/v1/PHASES_OVERVIEW.md` (dependency-ordered,
each decision cited `[id]`), `design-system/`, ADRs, `DATA_SOURCES.md`, and the
`LOOP_PROMPT.md` + `PROGRESS.md` for autonomous build. Then we gameplan V1.

**Fastest path:** reply with just the letters you want to *override* — everything
unanswered takes the ⭐. E.g. `P1→b, O2→c, A10→b`.

# Accounts & free-tier budget

> Inventory of services, the alias each uses, free limits, and the 80% budget alarms
> `[T10a,T9a]`. **No secrets here** — secrets live in GitHub Actions secrets + host env
> `[T7a]`. Inbound aliases route to one inbox via Cloudflare Email Routing catch-all
> `[T1d]`. 2FA (authenticator app) on every account `[T12a]`. Cite `BTB_QUESTIONNAIRE.md`.

## Only non-free item
**Custom domain ~$10/yr** `[T11a]` — pays for unlimited aliases + brand + email routing.
Everything else runs on free tier.

## Services

| Service | Alias | Free limit (watch) | 80% alarm at | Notes |
|---|---|---|---|---|
| Domain registrar | `admin@<domain>` | n/a (~$10/yr) | — | the one paid line |
| Cloudflare (Pages + R2 + Email Routing) | `cf@<domain>` | Pages build mins; R2 10 GB + free egress; unlimited email routes | R2 8 GB | host + blobs/tiles + catch-all `[P6a,O4d,T1d]` |
| Neon Postgres | `neon@<domain>` | **0.5 GB storage** | **400 MB** | small queryable state ONLY; bulk → R2/static `[O2a,L843]` |
| GitHub Actions | (repo) | 2,000 min/mo (private) | 1,600 min | ETL crons + CI gate; stagger nights `[T8a,R2a]` |
| `api.data.gov` (FEC + Census + Congress.gov) | `apidatagov@<domain>` | ~1,000 req/hr/key | watch 429s | one shared key `[T6a]` |
| Gmail (SMTP outbound alerts) | app-password | ~500 sends/day | 400/day | regression emails `[S9c,T4b]` |
| Resend (fallback outbound) | `resend@<domain>` | 3,000/mo | — | only if Gmail SMTP limits bite `[T4a-note]` |

## Keyless sources (no account)
538 CSV, Voteview, unitedstates/congress-legislators, Census TIGER/Line `[T6a]`.

## Budget discipline
- Track Actions minutes + API quota + R2 bandwidth; alert at 80% `[T9a]` (wired in
  `v1.10.4-budget-alarms`).
- Cache + conditional requests + backoff; stagger crons across nights to stay free
  `[T8a,R10a]`.
- Neon is the tight one — the 400 MB alarm is load-bearing; prune raw to R2 by `cycle`
  `[L843]` (ADR 0002).

# 0005 · Email aliases & outbound alerts

**Status:** Accepted · 2026-06-28

## Context
Signing up for many free services exhausts email addresses, and the loop must email the
maintainer on regression. Need unlimited inbound aliases + reliable outbound, free.

## Decision
**Inbound:** custom domain + **Cloudflare Email Routing catch-all** → unlimited
per-service aliases (`fec@`, `census@`…) → one inbox `[T1d]`. `+`-addressing as a backup
where catch-all is blocked `[T2b]`.
**Outbound (alerts/digests):** **Gmail SMTP with an app password** `[T4b,S9c]` — *not*
Resend (the earlier spine draft said Resend; the answered questionnaire selects Gmail
SMTP). Secret in GitHub Actions secrets `[T7a]`.

## Consequences
- Never "out of emails"; every service gets its own traceable alias.
- One Gmail app-password secret drives loop/QA alerts (summary + diff + run link +
  severity) `[S10a]`.
- If Gmail SMTP limits bite, Resend (free 3k/mo) is the documented fallback `[T4a-note]`.

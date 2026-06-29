# Setup — GitHub secrets (email + Actions) and the other blockers

Step-by-step to put the credentials the build loop needs into GitHub, plus a links
section for the remaining provisioning. Companion to [`ACCOUNTS.md`](./ACCOUNTS.md)
(service inventory + free limits). **Secrets never go in git** — only in GitHub
Actions secrets and host env `[T7a]`.

---

## 0. Where secrets live

GitHub → your repo → **Settings → Secrets and variables → Actions**.

Two kinds:
- **Secrets** (encrypted, write-only after save) — anything sensitive: keys, tokens,
  passwords, DB URLs.
- **Variables** (plain, readable) — non-sensitive config: the alert recipient, SMTP
  host/port.

Fast path is the `gh` CLI (authenticate once with `gh auth login`):

```bash
# from the repo root
gh secret set SMTP_USER          # prompts for the value, hidden
gh secret set SMTP_PASS
gh variable set ALERT_EMAIL_TO --body "alerts@yourdomain"
gh secret list                   # confirm names (values never shown)
```

> If a workflow should only run secrets in a protected context, use an **Environment**
> (Settings → Environments) and set the secret there instead of repo-wide. For this
> project, repo-level Actions secrets are fine.

---

## 1. Email — Gmail SMTP app password

Outbound alert emails (regression alerts `v1.10.3`, weekly review `v1.10.5`) send via
Gmail SMTP `[S9c,T4b]`. Gmail blocks plain-password SMTP — you need an **app password**,
which requires 2-Step Verification on the account.

1. **Turn on 2-Step Verification** (required for app passwords):
   <https://myaccount.google.com/signinoptions/twosv>
2. **Create an app password** (pick "Mail" / "Other → behind-the-ballot"):
   <https://myaccount.google.com/apppasswords>
   → Google shows a **16-character** password once. Copy it (spaces don't matter).
3. Put it in GitHub:

   ```bash
   gh secret set SMTP_USER --body "youraccount@gmail.com"
   gh secret set SMTP_PASS --body "the16charapppassword"
   ```

4. Non-secret SMTP config as **variables** (so the workflow has host/port/recipient):

   ```bash
   gh variable set SMTP_HOST --body "smtp.gmail.com"
   gh variable set SMTP_PORT --body "587"          # STARTTLS
   gh variable set ALERT_EMAIL_TO --body "you@yourdomain"
   ```

| Name | Kind | Example | Used by |
|---|---|---|---|
| `SMTP_USER` | secret | `you@gmail.com` | alert email auth |
| `SMTP_PASS` | secret | 16-char app password | alert email auth |
| `SMTP_HOST` | variable | `smtp.gmail.com` | alert email transport |
| `SMTP_PORT` | variable | `587` | alert email transport |
| `ALERT_EMAIL_TO` | variable | `you@yourdomain` | alert recipient |

**Limits:** ~500 sends/day; alarm at 400/day `[T4b]`. If that bites, Resend is the
documented fallback (`ACCOUNTS.md`).

**Quick local test** (verifies the app password before trusting a cron):

```bash
python3 - <<'PY'
import os, smtplib
from email.message import EmailMessage
m = EmailMessage()
m["From"] = os.environ["SMTP_USER"]; m["To"] = os.environ.get("ALERT_EMAIL_TO", os.environ["SMTP_USER"])
m["Subject"] = "behind-the-ballot SMTP test"; m.set_content("It works.")
with smtplib.SMTP("smtp.gmail.com", 587) as s:
    s.starttls(); s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"]); s.send_message(m)
print("sent")
PY
```

Run it with the values exported in your shell (not committed). A successful send means
the app password is good.

---

## 2. GitHub Actions — consuming the secrets

Actions runs the ETL crons + CI gate + alert/QA workflows `[T8a,R2a]`. Secrets are
**not** auto-exposed — each workflow maps the ones it needs into `env`.

```yaml
# .github/workflows/<job>.yml
jobs:
  alert:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: send regression alert
        env:
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASS: ${{ secrets.SMTP_PASS }}
          SMTP_HOST: ${{ vars.SMTP_HOST }}
          SMTP_PORT: ${{ vars.SMTP_PORT }}
          ALERT_EMAIL_TO: ${{ vars.ALERT_EMAIL_TO }}
        run: uv run python -m pipeline.alerts
```

Rules that bite if ignored:
- `secrets.*` for secrets, `vars.*` for variables — they are different namespaces.
- Secrets are **masked** in logs (printed value shows `***`) but never log them anyway.
- A workflow triggered from a **fork PR** cannot read repo secrets — the nightly/cron
  and `push`-to-`dev` jobs can, which is what this project uses.
- Scheduled jobs use `on: schedule: - cron: '...'` (UTC). Stagger across nights to stay
  under 2,000 Actions min/mo `[T8a]`.

Set the data/deploy secrets the same way (full list in §3 / `ACCOUNTS.md`):

```bash
gh secret set DATA_GOV_API_KEY
gh secret set CLOUDFLARE_API_TOKEN
gh secret set CLOUDFLARE_ACCOUNT_ID
gh secret set R2_BUCKET
gh secret set DATABASE_URL
```

---

## 3. Links to complete the other blockers

Order: (1) and (3) unblock the most. Each ends in the GitHub secret name to set.

### Domain + Cloudflare Email Routing (~$10/yr — the only paid item) `[T11a,T1d]`
- Register a domain (any registrar; Cloudflare Registrar is at-cost):
  <https://dash.cloudflare.com/?to=/:account/registrar>
- Add the domain to Cloudflare, then **Email Routing → catch-all → your inbox**:
  <https://dash.cloudflare.com/?to=/:account/:zone/email/routing>
- After it resolves, update the canonical URL: `site` in
  `apps/web/astro.config.mjs` + `apps/web/public/robots.txt` (replace the placeholder).

### `api.data.gov` key (free, instant) — `DATA_GOV_API_KEY` `[T6a]`
- Sign up: <https://api.data.gov/signup/>. **Verified iter 60: this key works for FEC OpenFEC**
  (live bake = 200 rows). It does **NOT** work for `api.census.gov` (ACS) — that host needs its
  own key (below) and 302-redirects a data.gov key to `missing_key.html`.
- FEC OpenFEC docs: <https://api.open.fec.gov/developers/>
  ```bash
  gh secret set DATA_GOV_API_KEY
  ```

### Census API key (free, instant) — `CENSUS_API_KEY` (ACS demographics)
- `api.census.gov` requires its **own** key, separate from `DATA_GOV_API_KEY`.
- Sign up: <https://api.census.gov/data/key_signup.html> (Census docs:
  <https://www.census.gov/data/developers/data-sets.html>)
- The ACS connector reads `CENSUS_API_KEY`, falling back to `DATA_GOV_API_KEY` only for
  single-key setups (which won't authenticate against Census).
  ```bash
  gh secret set CENSUS_API_KEY
  ```

### Cloudflare Pages + R2 — `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `R2_BUCKET`
- **Pages** project (connect this repo; build `pnpm build`, output `apps/web/dist`):
  <https://dash.cloudflare.com/?to=/:account/pages/new>
- **R2** bucket (PMTiles + bulk blobs): <https://dash.cloudflare.com/?to=/:account/r2>
- **API token** (scope: Pages Edit + R2 Edit): <https://dash.cloudflare.com/profile/api-tokens>
- **Account ID**: on the dashboard right sidebar of any zone/account page.
  ```bash
  gh secret set CLOUDFLARE_API_TOKEN
  gh secret set CLOUDFLARE_ACCOUNT_ID
  gh secret set R2_BUCKET            # the bucket name
  ```
  This unblocks the **live preview URL** = the deploy gate the promise needs.

  **Workers Build settings (this repo deploys as a Workers Static-Assets project, a
  monorepo — get these exact):**

  | Setting | Value |
  |---|---|
  | Root directory | `/` (repo root) |
  | Build command | `pnpm install && pnpm build` |
  | Deploy command | `npx wrangler deploy` |
  | Production branch | `dev` (the loop's integration branch; `main` is walled `[S5a]`) |
  | Build variable | `NODE_VERSION` = `20` |

  The deploy is driven by **`wrangler.jsonc`** at the repo root (committed), which
  points Workers Static Assets at the build output:

  ```jsonc
  { "name": "behind-the-ballot", "compatibility_date": "2025-09-01",
    "assets": { "directory": "./apps/web/dist" } }
  ```

  > ⚠️ **"root directory not found"** came from setting Root directory to
  > `apps/web/dist`. `dist` is gitignored build *output*, not a source dir, so it isn't
  > in the clone. Root directory is where the build *runs* (repo root); the output dir
  > (`apps/web/dist`) is declared to wrangler via `assets.directory`, not as the Pages
  > "output directory" field. This is a **Workers Build** (`wrangler deploy`), not a
  > classic Pages project.

  **Worker runtime secrets: none.** The site is fully static — `DATA_GOV_API_KEY`,
  `DATABASE_URL`, SMTP, etc. are **build/ETL secrets used by GitHub Actions**, not by the
  Worker. So "Variables and secrets: None" on the Worker is correct; those secrets live
  in GitHub Actions (§0–§2).

  Manual/local deploy (what `scripts/resume.sh` runs; the connected Workers Build also
  auto-deploys on push to `dev`): `wrangler deploy`.

### Neon Postgres (free) — `DATABASE_URL` `[O2a]`
- Create a project, copy the pooled connection string:
  <https://console.neon.tech/signup>
  ```bash
  gh secret set DATABASE_URL        # postgres://...neon.tech/...?sslmode=require
  ```
- Watch the **0.5 GB** cap (alarm at 400 MB) — small queryable state only; bulk → R2.

### 2FA everywhere `[T12a]`
- Turn on authenticator-app 2FA for GitHub, Cloudflare, Neon, Google. GitHub:
  <https://github.com/settings/security>

---

## 4. Done check

```bash
gh secret list      # expect: DATA_GOV_API_KEY, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID,
                    #         R2_BUCKET, DATABASE_URL, SMTP_USER, SMTP_PASS
gh variable list    # expect: SMTP_HOST, SMTP_PORT, ALERT_EMAIL_TO
```

When these are in (and the domain points at Cloudflare), re-feed the build loop — it
detects the keys in CI and resumes real connectors + the Cloudflare deploy, which is what
flips the remaining 14 units green and lets the `V1 COMPLETE` self-check pass. Until then
the loop builds env-keyed connectors against fixtures.

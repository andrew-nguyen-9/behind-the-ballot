#!/usr/bin/env bash
# Resume driver — run once the accounts/secrets from docs/SETUP_SECRETS.md are in.
# Verifies env, runs the full local gate, then deploys apps/web/dist to Cloudflare Pages
# directly via wrangler (no git push → never touches the `main` wall [S5a]).
#
#   ./scripts/resume.sh            # gate + deploy
#   ./scripts/resume.sh --no-deploy  # gate only
#
# Secrets are read from the environment, or from a gitignored .env at repo root.
set -euo pipefail
cd "$(dirname "$0")/.."

# --- load .env if present (gitignored) -------------------------------------
if [[ -f .env ]]; then set -a; . ./.env; set +a; fi

# --- branch guard: the loop integrates on dev, main is human-only [S5a] ----
branch="$(git branch --show-current)"
[[ "$branch" == "dev" ]] || { echo "refusing: on '$branch', expected dev"; exit 1; }

# --- required secrets ------------------------------------------------------
required=(DATA_GOV_API_KEY CLOUDFLARE_API_TOKEN CLOUDFLARE_ACCOUNT_ID R2_BUCKET
          DATABASE_URL SMTP_USER SMTP_PASS)
missing=()
for v in "${required[@]}"; do [[ -n "${!v:-}" ]] || missing+=("$v"); done
if (( ${#missing[@]} )); then
  printf 'missing secrets: %s\n' "${missing[*]}"
  echo 'set them (export or .env) — see docs/SETUP_SECRETS.md'; exit 1
fi
echo "✓ all ${#required[@]} secrets present"

# --- python gate -----------------------------------------------------------
echo "== python: pytest + ruff =="
uv run --project pipeline pytest -q
uv run --project pipeline ruff check pipeline

# --- web gate --------------------------------------------------------------
echo "== web: install + check + test + build + links =="
pnpm install --frozen-lockfile
pnpm --filter web check
pnpm --filter web exec vitest run
pnpm build                       # astro build + pagefind → apps/web/dist
node scripts/check-links.mjs apps/web/dist

# --- a11y / perf gate (static dist, no live server) ------------------------
echo "== lighthouse (perf/a11y/best-practices/seo >= 0.9) =="
pnpm dlx @lhci/cli@0.14.x autorun --config=apps/web/lighthouserc.json

# --- deploy ----------------------------------------------------------------
if [[ "${1:-}" == "--no-deploy" ]]; then
  echo "gate green; --no-deploy set, stopping before deploy"; exit 0
fi
echo "== deploy: wrangler pages deploy =="
# CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID are read from env by wrangler.
pnpm dlx wrangler@3 pages deploy apps/web/dist \
  --project-name=behind-the-ballot --branch=dev

echo "✓ resume complete — live preview deployed. Re-feed the loop to build the"
echo "  now-unblocked units (v1.1.6 live-bake → connectors → v1.10.x crons)."

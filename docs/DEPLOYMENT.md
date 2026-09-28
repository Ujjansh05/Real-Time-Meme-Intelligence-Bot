# Deploying Humour Hub's free public beta

The extension runs locally in the browser. AI and trend data come from the backend. This guide covers the Cloudflare Workers AI and Render option, which needs Render, Cloudflare, Upstash, and a GitHub repository with Actions enabled. For AI on your own Windows computer, follow [LOCAL_AI.md](LOCAL_AI.md). Use free service plans and leave paid upgrades disabled to honor the ₹0 budget.

## 1. Secure the repository

An environment file was tracked in an earlier revision. The current tree untracks it and ignores future `.env` files, but earlier Git history may still contain its values. Check any services that used those values and rotate the credentials before deploying. Never copy real keys into a GitHub issue, release artifact, or extension build.

## 2. Configure Cloudflare AI and Upstash

Create a Cloudflare API token scoped to Workers AI inference and note the account ID. Review the terms for the selected models. Llama 3.2 Vision requires an explicit first-run license acceptance request before image requests work. Cloudflare's free allocation resets daily; excess requests fail rather than triggering charges on the free plan.

Create an Upstash Redis Free database. Copy its HTTPS REST URL and REST token. Quotas and trend snapshots share the database. Generate a long random `SESSION_SECRET` for anonymous signed sessions; changing it invalidates existing sessions.

## 3. Deploy FastAPI on Render Free

Use the included [`render.yaml`](../render.yaml) Blueprint or create a Python web service from this repository, with root directory `Backend`, build command `pip install -r requirements.txt`, and start command `uvicorn app:app --host 0.0.0.0 --port $PORT --no-access-log`. Use Python 3.12. Set the variables from [`Backend/.env.example`](../Backend/.env.example) in Render's environment panel. Keep `AI_PROVIDER=cloudflare` and `QUOTA_BACKEND=upstash`. Supply Cloudflare and Upstash values; the Blueprint generates a session secret. Set `TRUST_PROXY_HEADERS=true` only on the public Render web service, where Render overwrites `CF-Connecting-IP`; this lets the per-network quota distinguish visitors. Set `AI_DISABLED=true` until the service is verified, then switch it to `false`.

Use `GET /api/v1/status` and `GET /api/v1/trends` as smoke checks. The Render free service sleeps when idle and its filesystem is temporary, so requests can be slow after inactivity. The API never relies on persistent local files.

## 4. Enable live sources

The [trend workflow](../.github/workflows/trends.yml) writes snapshots directly to Upstash. Add `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` as GitHub Actions secrets, then run the workflow manually with source `wikipedia` to create the first live result. Scheduled jobs refresh Wikipedia daily and social sources twice an hour; scheduling can be delayed.

For Reddit, obtain approval under Reddit's current Data API policy. Only then set GitHub variable `REDDIT_API_APPROVED=true`, secrets `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`, and variable `REDDIT_USER_AGENT` with contact information. `REDDIT_COMMUNITIES` can list up to five approved community names.

For Bluesky, create a dedicated service account and app password. Add secrets `BLUESKY_HANDLE` and `BLUESKY_APP_PASSWORD`; optionally set `BLUESKY_QUERIES`. Run the workflow manually with source `social`. Verify each source's `status`, `observed_at`, and source links from `/api/v1/trends` before enabling its card in a public announcement. Missing access leaves that source marked unavailable.

## 5. Package and distribute

Set the repository Actions variable `HUMOUR_HUB_API_URL` to the public HTTPS origin, without a trailing slash. The CI workflow then builds a Manifest V3 extension with that URL and publishes a versioned ZIP and SHA-256 checksum as workflow artifacts. Download the ZIP, extract it, and test it in clean Chrome and Edge profiles before attaching it to a GitHub Release or submitting it to Microsoft Edge Add-ons.

Store publication needs owner-operated accounts and store review. Edge developer enrollment currently has no registration fee; Chrome Web Store enrollment has a one-time fee. A Chrome ZIP is still freely downloadable but requires Load unpacked installation.

## 6. Operate and recover

Monitor `/api/v1/status`, the Render logs, Upstash usage, Cloudflare neuron usage, and trend timestamps. Avoid logging submitted images or captions. On quota exhaustion, the extension should still edit and export memes locally. Set `AI_DISABLED=true` for an immediate AI pause; use Render's prior deploy rollback if a new backend version fails. If Redis is unavailable, hosted AI fails closed until storage recovers.

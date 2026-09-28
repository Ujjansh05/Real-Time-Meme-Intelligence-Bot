# Humour Hub

Humour Hub is a free, open-source Chrome and Edge extension for understanding and creating memes. Explain a caption or image, ask for three remixes in English, Hindi, or Hinglish, edit a meme, and download it as a PNG. Drafts and favorites stay in your browser. The AI features use a hosted API with a daily public beta allowance.

## Install

Public store links will be added here after approval. For a developer preview, download the production extension ZIP from a GitHub Release, extract it, open `chrome://extensions/` or `edge://extensions/`, enable Developer mode, and choose **Load unpacked** on the extracted folder. The ZIP must contain `manifest.json` at its top level. The local preview ZIP in `artifacts/` points to `127.0.0.1` and is only for testing on the developer's computer. See the [store submission guide](docs/STORE_SUBMISSION.md) for release steps and listing copy.

The extension's popup handles quick explanations and remixes. Open the full editor from the popup to compose images, keep drafts, and browse source-labeled trends. Only content you explicitly submit for AI is sent to the hosted API. [Privacy notice](PRIVACY.md).

## Run locally

Requirements: Python 3.12+, Node.js 22+, and npm.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r Backend\requirements.txt
python -m pip install pytest httpx
cd Backend
uvicorn app:app --reload --port 8000
```

In another terminal:

```powershell
cd extension
npm ci
npm run build
```

Load `extension/dist` as an unpacked extension. Without service credentials, editing and saved content work locally, while the API reports that AI is unavailable. `Backend/.env.example` lists the deployment settings; set them in the process environment or your hosting dashboard. The backend does not require users to supply API keys.

To build against a deployed API, set `VITE_API_BASE_URL` to its HTTPS origin before `npm run build`. This adds the matching host permission to the manifest. The CI ZIP artifact is created only when the repository variable `HUMOUR_HUB_API_URL` is set.

## Hosted services and limits

The public beta uses FastAPI, Cloudflare Workers AI, and Upstash Redis. Set a Cloudflare account ID and API token, Upstash REST URL and token, a random session signing secret, and the production extension origin in the backend environment. The server enforces daily limits of five AI actions per installation, twenty per network address, and one hundred across the service. Provider free-tier exhaustion may stop requests earlier. The meme editor and local library continue to work.

Cloudflare's Llama 3.2 Vision model requires the deployer to review and accept its license before the first image request. See [third-party notices](THIRD_PARTY_NOTICES.md). Do not enable a paid plan to maintain the intended ₹0 operating budget.

## Live discovery

Trend cards show their source and last observation time. Wikipedia interest tracks changes in readership of known meme articles. Reddit and Bluesky integrations are optional and need approved or working source access. If a source is unavailable, the UI says so; it never invents a trend. The collector is designed for scheduled runs and persists snapshots in Redis. See [deployment guide](docs/DEPLOYMENT.md) for the source configuration and scheduled job.

## Development and checks

```powershell
python -m pytest -q Backend
cd extension
npm run check
npm run build
```

The API exposes `POST /api/v1/session`, `POST /api/v1/explain`, `POST /api/v1/remix`, `GET /api/v1/trends`, and `GET /api/v1/status`. API documentation is available at `/docs` when the backend runs. Anonymous session tokens go in the `Authorization: Bearer` header for AI requests. Legacy routes remain as compatibility adapters.

Security reports can be sent privately through GitHub's repository security advisory feature. Do not post keys or private meme content in public issues. This project is licensed under [MIT](LICENSE).

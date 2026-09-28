# Run Humour Hub AI on your Windows computer

This setup uses Ollama for inference. The extension still talks only to Humour Hub's FastAPI backend. The backend talks to Ollama at `127.0.0.1:11434`; do not publish Ollama's port to the internet.

For a computer with 16 GB RAM and an NVIDIA RTX 3050 6 GB, start with [`qwen2.5vl:3b`](https://ollama.com/library/qwen2.5vl:3b). Its download is about 3.2 GB, it accepts text and images, and Ollama lists its license as Apache 2.0. Runtime memory also depends on image size and context. The backend handles one Ollama request at a time and returns a busy message if the short queue is full. Expect a small beta audience rather than unlimited simultaneous users.

## 1. Install and test Ollama

Install [Ollama for Windows](https://docs.ollama.com/windows), then open a new PowerShell window:

```powershell
ollama pull qwen2.5vl:3b
ollama run qwen2.5vl:3b
```

Ask it a short question, then type `/bye`. Ollama's API normally runs at `http://127.0.0.1:11434`. Check that the model appears:

```powershell
(Invoke-RestMethod http://127.0.0.1:11434/api/tags).models.name
```

The model download and first inference can take time. `ollama ps` shows whether the model is running on the GPU or CPU.

## 2. Test Humour Hub locally, without cloud AI or Redis

Use the existing Python environment in the repository. In one PowerShell window, set these variables for **this window only** and start the backend:

```powershell
cd C:\Users\ujjan\Real-Time-Meme-Intelligence-Bot\Backend
$env:AI_PROVIDER = 'ollama'
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
$env:OLLAMA_MODEL = 'qwen2.5vl:3b'
$env:QUOTA_BACKEND = 'memory'
$env:SESSION_SECRET = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
$env:AI_DISABLED = 'false'
..\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --no-access-log
```

In another window, visit `http://127.0.0.1:8000/api/v1/status`. It should report `ai_provider: ollama`, `ai_available: true`, and `quota_available: true`. Load `extension/dist` in Chrome or Edge, add sample text, check the AI consent box, and click **Explain**. The local build already points to `127.0.0.1:8000`.

The memory quota is for a single local process. Counts disappear when the backend restarts. The editor and local library work even when Ollama is stopped.

To check the API from a phone or another network before setting up a stable hostname, the already installed `cloudflared` can create a temporary test URL:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

The printed `trycloudflare.com` address changes and [Quick Tunnels are for development only](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/). Do not put that address in a store extension.

## 3. Serve a small public beta without a domain

[Tailscale Funnel](https://tailscale.com/docs/features/tailscale-funnel) can publish the local FastAPI port at a stable `https://...ts.net` name. This is suitable for a small, noncommercial beta; review Tailscale's current [Personal plan terms and bandwidth limits](https://tailscale.com/pricing). A public extension needs a stable URL, so a changing Cloudflare Quick Tunnel URL is only useful for temporary testing.

Create an [Upstash Redis Free](https://upstash.com/docs/redis/overall/getstarted) database for persistent, shared quotas. In the PowerShell window that starts FastAPI, use the following settings. Store the actual tokens outside the repository and set them in that window or a private startup script. Keep the same `SESSION_SECRET` across restarts so existing sessions remain valid.

```powershell
$env:AI_PROVIDER = 'ollama'
$env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
$env:OLLAMA_MODEL = 'qwen2.5vl:3b'
$env:QUOTA_BACKEND = 'upstash'
$env:UPSTASH_REDIS_REST_URL = '<your Upstash HTTPS REST URL>'
$env:UPSTASH_REDIS_REST_TOKEN = '<your Upstash REST token>'
$env:SESSION_SECRET = '<your stable random 64-character secret>'
$env:TRUST_PROXY_HEADERS = 'false'
$env:IP_DAILY_LIMIT = '100'
$env:GLOBAL_DAILY_LIMIT = '100'
$env:AI_DISABLED = 'false'
..\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --no-access-log
```

Use `IP_DAILY_LIMIT=100` here because Funnel's local proxy address may appear as the same network address for all visitors. The installation limit of five and global limit of 100 still apply. Do not set `TRUST_PROXY_HEADERS=true` with Funnel: Humour Hub only trusts Cloudflare's `CF-Connecting-IP` header, which Funnel does not provide.

Install [Tailscale for Windows](https://tailscale.com/download/windows) and sign in on this PC, enable Funnel for your tailnet, then run in another PowerShell window:

```powershell
tailscale funnel 8000
```

Tailscale prints the public HTTPS URL. From a different internet connection, check `https://your-machine.your-tailnet.ts.net/api/v1/status`, then test one consented AI request in a locally built extension configured for that URL. Keep Ollama, FastAPI, Tailscale, and the PC running. Do not expose port `11434` or `8000` through router port forwarding; Funnel connects to the loopback API.

Once the HTTPS URL is stable, set the repository Actions variable `HUMOUR_HUB_API_URL` to that origin, run **Verify and package**, and test the resulting ZIP in a clean browser profile. The store submission steps are in [STORE_SUBMISSION.md](STORE_SUBMISSION.md). If the Funnel hostname changes, rebuild and redistribute the extension.

## Alternative with your own domain

If you later add a domain to Cloudflare, use a [named Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/) to route `api.yourdomain.com` to `http://127.0.0.1:8000`. Keep the backend bound to loopback. You may set `TRUST_PROXY_HEADERS=true` only when the named tunnel is the sole public path to the backend, because Cloudflare supplies `CF-Connecting-IP`. Set `IP_DAILY_LIMIT` back to `20` if per-network limits work as intended. Cloudflare's free Quick Tunnels have random hostnames and are explicitly for testing, so do not build a store extension against one.

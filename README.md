
# 🤖 Humour Hub
<img width="858" height="852" alt="Gemini_Generated_Image_7lbzm37lbzm37lbz" src="https://github.com/user-attachments/assets/50f6e0e2-fd19-4645-9640-4b7f8bc7ac92" />

A fun and innovative project built for the **Pathway X Iota Cluster IIT Ropar Gen AI Hackathon** 🎉

This bot transforms memes into an interactive experience:
- 🔥 Detects **trending meme formats** in real-time
- 📝 **Explains memes** (for people who don’t get the reference)
- 🎭 **Remixes memes** into new contexts (e.g., IIT student life, wholesome version)
- 🧩 Works as a **browser extension** for quick, efficient usage

---

### 🌟 Features
- **Real-Time Ingestion with Pathway** → continuously streams meme captions from APIs or mock feeds
- **Dynamic RAG Pipeline** → keeps knowledge always updated with the latest memes
- **Trend Detection** → identifies the fastest-growing meme clusters
- **Meme Explanation** → explains the cultural or humorous reference behind a meme
- **Meme Remixing** → generates new versions of memes in different styles
- **Browser Extension (Chrome/Edge)** → easy to use while scrolling Twitter/Reddit

---

### ⚡ Tech Stack
- **[Pathway](https://github.com/pathwaycom/pathway)** → real-time data ingestion, indexing, and streaming analytics
- **FastAPI** → backend to serve REST APIs (`/trending`, `/explain`, `/remix`,`/explain-image`)
- **Google Gemini AI** → State-of-the-art model for multimodal meme explanation and remix generation.
- **Chrome Extension (Manifest V3)** → Intuitive popup UI and seamless browser integration.

---

### 🚀 Getting Started

#### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/humor-hub.git](https://github.com/your-username/humor-hub.git)
cd humor-hub
````

#### 2\. Backend Setup

Navigate to the `backend` folder and install dependencies:

```bash
# Real-Time Meme Intelligence Bot

A lightweight project that ingests meme captions, detects trending formats and exposes a small FastAPI backend plus a browser extension UI.

This repository contains a compact backend (FastAPI + ingestion pipeline) and a Chrome/Edge extension to interact with the service.

Key behaviors in this workspace:
- ingest meme captions (mock/static CSV data in `Backend/data/`)
- a pipeline script that processes incoming captions (`Backend/pathway_pipeline.py`)
- a FastAPI app in `Backend/app.py` exposing simple endpoints
- a browser extension in `extension/` that calls the backend APIs

> Note: For convenience the dataset `Backend/data/memes.csv` has been trimmed to unique entries.

## Quick start (Windows PowerShell)

1. Create and activate a virtual environment, then install dependencies:

```powershell
cd "c:\Users\ujjan\OneDrive\Desktop\python_projects\GGWave\Real-Time-Meme-Intelligence-Bot"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r Backend\requirements.txt
```

2. Run the ingestion pipeline (optional) and the API server. Open two PowerShell terminals.

Terminal A — run the pipeline (simulates ingestion / trend updates):

```powershell
cd Backend
python pathway_pipeline.py
```

Terminal B — run the FastAPI server (from the `Backend` folder so imports work as-is):

```powershell
cd Backend
uvicorn app:app --reload --port 8000
```

The API will be available at: http://localhost:8000

### Common API endpoints (provided by `Backend/app.py`)
- GET /trending — returns current top trending meme format(s)
- GET /explain?meme=<text> — returns an explanation for a meme caption
- GET /remix?meme=<text> — returns a short remix for a caption

(Exact endpoint names and parameters depend on `Backend/app.py` implementation; check that file for the definitive contract.)

## Browser extension (local load)

1. Open Chrome/Edge and navigate to `chrome://extensions/`.
2. Enable **Developer mode**.
3. Click **Load unpacked** and select the `extension/` folder from the repo root.
4. Use the popup UI to call the backend APIs.

## Data

- `Backend/data/memes.csv` — mock dataset of meme captions and formats (now deduplicated).
- `Backend/data/live_meme.csv`, `trending.jsonl`, `trending_formats.jsonl` — other data/artifacts used by the ingestion pipeline.

If you want to reset `memes.csv` to its original raw copy, keep a backup before running automated transforms.

## Project structure

```
Real-Time-Meme-Intelligence-Bot/
├─ Backend/
│  ├─ app.py                 # FastAPI app
│  ├─ pathway_pipeline.py    # ingestion / processing pipeline (simulated)
│  ├─ reddit_stream.py       # optional helper to stream from Reddit (if configured)
│  ├─ requirements.txt       # Python dependencies
│  └─ data/                  # sample and runtime data
│     ├─ memes.csv
│     ├─ live_meme.csv
│     ├─ trending.jsonl
│     └─ trending_formats.jsonl
├─ extension/
│  ├─ background.js
│  ├─ popup.html
│  ├─ popup.js
│  ├─ manifest.json
│  └─ icon.png
└─ README.md
```

## Notes, assumptions and next steps

- Assumption: environment secrets (API keys) are configured outside this repo or added by you. There is no checked-in `.env` file in `Backend/` in the current workspace; if your code expects keys, create a `.env` or configure them in your shell.
- If you want the repo to connect to live sources (Reddit, Twitter), add credentials and enable the corresponding code paths in `Backend/reddit_stream.py` or `pathway_pipeline.py`.
- I can add a small `scripts/dedupe_memes.py` utility to make deduplication repeatable, and create a `Backend/.env.example` if you want.

## Contributing

Feel free to open issues or pull requests. If you want me to add automated tests or a small utility script to (re)generate the extension package, tell me what behavior you'd like.

## License

MIT

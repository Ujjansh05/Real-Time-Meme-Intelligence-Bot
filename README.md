
# 🤖 Real-Time Meme Intelligence Bot

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
- [Pathway](https://github.com/pathwaycom/pathway) → real-time data ingestion, indexing, and streaming analytics
- **FastAPI** → backend to serve REST APIs (`/trending`, `/explain`, `/remix`)
- **OpenAI GPT (or any LLM)** → meme explanation and remix generation
- **Chrome Extension (Manifest V3)** → popup UI + context menu integration
- **Streamlit/React (Optional)** → dashboard for live demo visualizations

---

### 🚀 Getting Started

#### 1. Clone the Repository
```bash
git clone [https://github.com/](https://github.com/)<your-username>/meme-intelligence-bot.git
cd meme-intelligence-bot
````

#### 2\. Backend Setup

Navigate to the `backend` folder and install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Run the FastAPI server:

```bash
python app.py
```

By default, the API runs at: 👉 `http://localhost:8000`

APIs available:

  - `/trending` → returns current trending meme format
  - `/explain?meme=<text>` → explains the given meme caption
  - `/remix?meme=<text>` → generates a remix of the meme

#### 3\. Load the Browser Extension

1.  Open Chrome/Edge and go to `chrome://extensions/`
2.  Enable **Developer Mode**
3.  Click **Load Unpacked**
4.  Select the `extension/` folder
    Now you’ll see the Meme Bot icon in your browser toolbar 🎉

#### 4\. Using the Extension

  - Click the extension icon to open the popup.
  - **Buttons available:**
      - **Trending Meme** → fetch today’s trending meme format
      - **Explain Meme** → paste meme caption → get explanation
      - **Remix Meme** → paste meme caption → generate a remix
  - **Optional:** Highlight a meme caption → right-click → "Explain with Meme Bot"

-----

### 📂 Project Structure

```
meme-intelligence-bot/
│── backend/
│   ├── app.py               # FastAPI backend (API endpoints)
│   ├── pathway_pipeline.py  # Pathway ingestion + trend detection
│   ├── requirements.txt     # Python dependencies
│   └── data/memes.csv       # Mock streaming meme dataset
│
│── extension/
│   ├── manifest.json        # Chrome extension config
│   ├── popup.html           # Extension popup UI
│   ├── popup.js             # API calls to backend
│   ├── background.js        # (Optional) context menu logic
│   └── icon.png             # Extension icon
│
│── demo/
│   ├── demo.gif             # Demo GIF for quick preview
│   └── demo.mp4             # Demo video for hackathon submission
│
│── README.md                # Documentation
```

-----

### 🎬 Demo Workflow

1.  Add a new meme caption to `memes.csv` (or stream from Reddit/Twitter APIs).
2.  Pathway ingests it instantly → updates the trending index.
3.  Ask the extension: “What’s trending now?” → it reflects the new meme format.
4.  Paste a meme → Explain → AI describes why it’s funny.
5.  Hit Remix → AI generates a new caption (e.g., IIT life version).
6.  (Optional) Auto-generate meme images with Stable Diffusion for extra flair.

-----

### 🏆 Hackathon Highlights

  - Showcases **real-time AI** with Pathway
  - Combines fun + creativity + technical depth
  - Extension interface → makes the solution practical and user-friendly
  - Easy demo: judges will see memes appear live → instantly explained/remixed

-----

### 📌 Future Improvements

  - 🔮 Integrate Stable Diffusion API for meme image generation
  - 🌍 Multi-language meme explanations
  - 🗳 Meme popularity voting system inside the extension
  - 🧠 Smarter clustering of meme formats over time

-----

### 🤝 Contributors

UjjanshSundram (The Og one)

-----

### 📜 License

MIT License – feel free to use and remix memes responsibly 🙃

```
```

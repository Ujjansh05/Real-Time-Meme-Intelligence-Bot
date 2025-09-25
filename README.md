
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
- [Pathway](https://github.com/pathwaycom/pathway) → real-time data ingestion, indexing, and streaming analytics
- **Pathway** → Real-time data ingestion, trend calculation, and streaming analytics.
- **FastAPI** → backend to serve REST APIs (`/trending`, `/explain`, `/remix`,`/explain-image`)
- **Google Gemini AI** → State-of-the-art model for multimodal meme explanation and remix generation.
- **Chrome Extension (Manifest V3)** → Intuitive popup UI and seamless browser integration.

---

### 🚀 Getting Started

#### 1. Clone the Repository
```bash
it clone [https://github.com/your-username/humor-hub.git](https://github.com/your-username/humor-hub.git)
cd humor-hub
````

#### 2\. Backend Setup

Navigate to the `backend` folder and install dependencies:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Create a .env file from the example and add your Gemini API Key.
```bash
cp .env.example .env
nano .env 
# -> Set GEMINI_API_KEY="YOUR_API_KEY_HERE"
```

Run the two backend servers in separate terminals:
Terminal 1 (Start the Pathway Pipeline):
```bash
python pathway_pipeline.py
```
Terminal 2 (Start the FastAPI Server):
```bash
uvicorn app:app --reload
```


By default, the API runs at: 👉 `http://localhost:8000`

APIs available:

  - `/trending` → returns current trending meme format
  - `/explain?meme=<text>` → explains the given meme caption
  - `/remix?meme=<text>` → generates a remix of the meme
  - `/explain-image` → Explains a meme from pasted image data.

#### 3\. Load the Browser Extension

1.  Open Chrome/Edge and go to `chrome://extensions/`
2.  Enable **Developer Mode**
3.  Click **Load Unpacked**
4.  Select the `extension/` folder
    Now you’ll see the  Humor Hub icon in your browser toolbar 🎉

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
humor-hub/
│── backend/
│   ├── app.py              # FastAPI backend (API endpoints)
│   ├── pathway_pipeline.py   # Pathway ingestion + trend detection
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Example environment file
│   └── data/
│       └── memes.csv         # Mock streaming meme dataset
│
│── extension/
│   ├── manifest.json         # Chrome extension config
│   ├── popup.html            # Extension popup UI
│   ├── popup.js              # API calls and frontend logic
│   └── icon.png              # Extension icon
│
└── README.md                 # Project documentation
```

-----

### 🎬 Demo Workflow

1.  Add a new meme to `backend/data/memes.csv` to simulate a live event.
2.  Pathway ingests it instantly and updates the trending index in real-time.
3.  Ask the extension: “What’s trending now?” → it immediately reflects the new meme format.
4.  Paste a meme → Explain → AI describes why it’s funny.
5.  Hit Remix → AI generates a new caption (e.g., IIT life version).
6.  (Future Scope) Auto-generate meme images with Stable Diffusion for extra flair.

-----

### 🏆 Hackathon Highlights

  - Showcases **real-time AI** with Pathway
  - Combines fun + creativity + technical depth
  - Extension interface → makes the solution practical and user-friendly
  - Easy demo: judges will see memes appear live → instantly explained/remixed

-----

### 📌 Future Improvements

  - 🔮 AI Image Generation: Integrate a model like Imagen to generate new meme images from text prompts.
  - 🌍 Multi-Language Support: Expand the AI prompts to provide meme explanations in multiple languages.
  - 🗳 User Feedback System: Implement a voting system inside the extension for users to rate the quality of AI explanations.
  - 🧠 Automated Data Ingestion: Connect the Pathway pipeline to a live source like the Reddit API for fully autonomous trend detection.

-----

### 🤝 Contributors

UjjanshSundram (The Og one)

-----

### 📜 License

MIT License – feel free to use and remix memes responsibly 🙃

```
```

# ...existing code...
import csv, json
from datetime import datetime
from pathlib import Path
from scores import compute_trending  # existing scorer

DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "live_memes.csv"
OUT_PATH = DATA_DIR / "trending_formats.jsonl"

def load_live_memes():
    rows = []
    if not CSV_PATH.exists():
        return rows
    with CSV_PATH.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            ts = r.get("timestamp") or ""
            try:
                ts_dt = datetime.fromisoformat(ts)
            except Exception:
                ts_dt = datetime.utcnow()
            rows.append({
                "caption": (r.get("caption") or "").strip(),
                "format": (r.get("format") or "unknown").strip(),
                "timestamp": ts_dt,
                "engagement": int(r.get("engagement") or 0)
            })
    return rows

def group_by_format(rows):
    grouped = {}
    for r in rows:
        fmt = r["format"] or "unknown"
        grouped.setdefault(fmt, []).append({"timestamp": r["timestamp"], "engagement": r["engagement"]})
    return grouped

def run_trending_job():
    rows = load_live_memes()
    formats = group_by_format(rows)  # dict: format_name -> list of item dicts
    # compute_trending expects formats mapping; adapt if necessary
    scores = compute_trending(formats)  # returns {format_name: score}
    # write JSONL lines with count/diff/time
    now_ms = int(datetime.utcnow().timestamp() * 1000)
    with OUT_PATH.open("w", encoding="utf-8") as out:
        for fmt, score in sorted(scores.items(), key=lambda kv: -kv[1]):
            count = len(formats.get(fmt, []))
            obj = {"format": fmt, "count": count, "score": round(score, 3), "time": now_ms}
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")

# ...existing code...
if __name__ == "__main__":
    run_trending_job()
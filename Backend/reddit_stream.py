import praw
import pandas as pd
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Load Reddit API credentials securely from environment variables ---
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# --- Validation ---
if not all([CLIENT_ID, CLIENT_SECRET, USER_AGENT]):
    raise RuntimeError("Reddit API credentials not found in .env file. Please check your configuration.")

# --- Configuration ---
SUBREDDIT_TO_MONITOR = "memes"
OUTPUT_CSV_FILE = os.path.join("data", "live_memes.csv")

def initialize_reddit():
    """Initializes and returns a Reddit instance."""
    return praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent=USER_AGENT,
    )

def main():
    """
    Continuously streams new posts from a subreddit and saves them to a CSV file.
    """
    print("Starting Reddit data stream...")
    reddit = initialize_reddit()
    subreddit = reddit.subreddit(SUBREDDIT_TO_MONITOR)
    
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(OUTPUT_CSV_FILE), exist_ok=True)

    # Write header if file doesn't exist
    if not os.path.exists(OUTPUT_CSV_FILE):
        pd.DataFrame(columns=["caption", "format", "timestamp"]).to_csv(
            OUTPUT_CSV_FILE, index=False
        )
    
    print(f"Monitoring r/{SUBREDDIT_TO_MONITOR} for new posts...")
    
    for submission in subreddit.stream.submissions(skip_existing=True):
        try:
            new_row = {
                "caption": submission.title,
                "format": submission.link_flair_text or "unknown", # Use flair as format
                "timestamp": datetime.utcfromtimestamp(submission.created_utc).isoformat(),
            }

            df_new = pd.DataFrame([new_row])
            df_new.to_csv(OUTPUT_CSV_FILE, mode='a', header=False, index=False)
            
            print(f"New Post Added: '{submission.title}'")

        except Exception as e:
            print(f"An error occurred: {e}")
        
        time.sleep(1)


if __name__ == "__main__":
    main()


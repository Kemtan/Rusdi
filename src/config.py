import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN  = os.getenv("DISCORD_TOKEN")
CHANNEL_ID     = os.getenv("DISCORD_CHANNEL_ID")

REDDIT_SUBREDDIT  = os.getenv("REDDIT_SUBREDDIT")
REDDIT_CHANNEL_ID = os.getenv("REDDIT_CHANNEL_ID")
REDDIT_USERNAMES = os.getenv("REDDIT_USERNAMES", "")
REDDIT_USERNAMES = [u.strip() for u in REDDIT_USERNAMES.split(",") if u.strip()]

GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER   = os.getenv("GITHUB_OWNERS")
GITHUB_REPO    = os.getenv("GITHUB_REPOS")
GITHUB_BRANCH  = os.getenv("GITHUB_BRANCH")

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
WAVELINK_PASS   = os.getenv("WAVELINK_PASS")
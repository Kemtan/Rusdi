import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN       = os.getenv("DISCORD_TOKEN")
CHANNEL_ID          = os.getenv("DISCORD_CHANNEL_ID")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER   = os.getenv("GITHUB_OWNERS")
GITHUB_REPO    = os.getenv("GITHUB_REPOS")
GITHUB_BRANCH  = os.getenv("GITHUB_BRANCH")
import aiohttp
import sqlite3
import config

BASE_URL = "https://api.github.com"
GITHUB_TOKEN = config.GITHUB_TOKEN
DB_PATH = "github.db"

conn = sqlite3.connect(DB_PATH)
conn.execute(
    "CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)"
)
conn.commit()

def get_state(key: str):
    cur = conn.execute("SELECT value FROM state WHERE key = ?", (key,))
    row = cur.fetchone()
    return row[0] if row else None

def set_state(key: str, value: str):
    conn.execute(
        "INSERT INTO state(key, value) VALUES(?, ?)"
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )

    conn. commit()

# Fetch latest commit from Github
async def fetch_latest_commit(GITHUB_OWNER, GITHUB_REPO):
    
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print("Github error:", resp.status)
                return None
            data = await resp.json()
    
    return data[0]["sha"] if data else None

async def check_new_commit():

    latest_sha = await fetch_latest_commit(config.GITHUB_OWNER, config.GITHUB_REPO)
    if latest_sha is None:
        return None

    stored_sha = get_state("last_commit_sha")

    if stored_sha is None:
        set_state("last_commit_sha", latest_sha)
        return None
    
    if latest_sha != stored_sha:
        old = stored_sha
        set_state("last_commit_sha", latest_sha)
        return (old, latest_sha)
    
    return None
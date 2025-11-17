from datetime import datetime, timedelta
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
        "INSERT INTO state(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()

# Fetch latest commit from Github
async def fetch_latest_commit(GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH):
    
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits?sha={GITHUB_BRANCH}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0",
    }

    if GITHUB_TOKEN:
        headers["authorization"] = f"Bearer {config.GITHUB_TOKEN}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print("Github error:", resp.status)
                return None
            data = await resp.json()
    
    if isinstance(data, list) and len(data) > 0:
        commit = data[0]

        sha = commit["sha"]
        committer = commit["commit"]["committer"]["name"]
        message = commit["commit"]["message"]
        utc_time = commit["commit"]["committer"]["date"]

        # convert UTC to WIB (UTC+7)
        dt_utc = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%SZ")
        dt_wib = dt_utc + timedelta(hours=7)
        time_wib = dt_wib.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "sha": sha,
            "committer": committer,
            "message": message,
            "time_wib": time_wib,
        }

    return None

async def check_new_commit():
    latest = await fetch_latest_commit(config.GITHUB_OWNER, config.GITHUB_REPO, config.GITHUB_BRANCH)
    if latest is None:
        return None

    latest_sha = latest["sha"]
    stored_sha = get_state("last_commit_sha")

    # first run
    if stored_sha is None:
        set_state("last_commit_sha", latest_sha)
        return None
    
    # new commit detected
    if latest_sha != stored_sha:
        set_state("last_commit_sha", latest_sha)
        return latest
    
    return None
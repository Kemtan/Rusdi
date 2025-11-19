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

#-------------------------------------------------------------------------
async def fetch_user_events(username:str):

    url = f"https://api.github.com/users/{username}/events/public"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0",
    }

    if GITHUB_TOKEN:
        headers["authorization"] = f"Bearer {config.GITHUB_TOKEN}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params={"per_page": 30}) as resp:
            if resp.status != 200:
                print("Github events error:", resp.status)
                return []
            return await resp.json()
        
def _format_event(ev):
    ev_type = ev.get("type")
    repo = ev.get("repo", {}).get("name", "unknown/repo")
    created_at = ev.get("created_at")  # "2025-11-19T03:00:00Z"

    # time: UTC -> WIB
    time_wib = None
    if created_at:
        dt_utc = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
        dt_wib = dt_utc + timedelta(hours=7)
        time_wib = dt_wib.strftime("%Y-%m-%d %H:%M:%S")

    # simple per-type formatting
    if ev_type == "PushEvent":
        commits = ev.get("payload", {}).get("commits") or []
        if commits:
            last = commits[-1]
            msg = last.get("message", "(no message)")
        else:
            msg = "(no commits?)"
        text = f"New commit in `{repo}`\n`{msg}`"

    elif ev_type == "WatchEvent":
        text = f"Starred `{repo}`"

    elif ev_type == "PullRequestEvent":
        action = ev.get("payload", {}).get("action", "?")
        pr = (ev.get("payload", {})
                .get("pull_request", {})
                .get("title", "(no title)"))
        text = f"PR {action} `{pr}` in `{repo}`"

    elif ev_type == "IssuesEvent":
        action = ev.get("payload", {}).get("action", "?")
        issue = (ev.get("payload", {})
                  .get("issue", {})
                  .get("title", "(no title)"))
        text = f"New issue {action} `{issue}` in `{repo}`"

    else:
        text = f"{ev_type} in `{repo}`"

    if time_wib:
        text += f"\nTime (WIB): {time_wib}"

    return {
        "id": ev.get("id"),
        "type": ev_type,
        "repo": repo,
        "time_wib": time_wib,
        "text": text,
    }

async def check_new_events(username:str):

    events = await fetch_user_events(username)
    if not events:
        return []
    
    last_id = get_state("last_event_id")

    if last_id is None:
        set_state("last_event_id", events[0]["id"])
        return []
    
    new_raw = []
    for ev in events:
        if ev.get("id") == last_id:
            break
        new_raw.append(ev)

    if not new_raw:
        return []
    
    new_raw.reverse()

    set_state("last_event_id", events[0]["id"])

    return [_format_event(ev) for ev in new_raw]
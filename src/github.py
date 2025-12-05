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

# ---------------- Webhook ----------------

def _to_wib(iso_utc: str) -> str:
    """Convert ISO timestamp (with Z or offset) to WIB formatted time."""
    try:
        # Case 1: UTC with Z suffix, e.g. 2025-12-05T09:28:22Z
        if iso_utc.endswith("Z"):
            dt_utc = datetime.strptime(iso_utc, "%Y-%m-%dT%H:%M:%SZ")
            dt_wib = dt_utc + timedelta(hours=7)
            return dt_wib.strftime("%Y-%m-%d %H:%M:%S")

        # Case 2: has explicit offset, e.g. 2025-12-05T16:28:22+07:00
        # datetime.fromisoformat can handle this directly
        from datetime import timezone
        dt = datetime.fromisoformat(iso_utc)
        if dt.tzinfo is None:
            # fallback if somehow naive
            dt = dt.replace(tzinfo=timezone.utc)
        wib = dt.astimezone(timezone(timedelta(hours=7)))
        return wib.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "unknown"


def format_push_embed(payload: dict) -> dict | None:
    """
    Convert GitHub push payload to a Discord embed dict.
    Returns None if payload isn't valid.
    """
    repo_full = payload.get("repository", {}).get("full_name")
    commits = payload.get("commits") or []
    sender = payload.get("sender", {})
    avatar = sender.get("avatar_url", "")

    if not repo_full or not commits:
        return None

    commit = commits[-1]
    sha = (commit.get("id") or "")[:7]
    msg = commit.get("message", "(no message)")
    url = commit.get("url", "")
    author_name = commit.get("author", {}).get("name", "unknown")
    timestamp = commit.get("timestamp")
    time_wib = _to_wib(timestamp) if timestamp else "unknown"

    owner, repo = repo_full.split("/", 1)

    embed = {
        "title": f"New Commit in {owner}/{repo}",
        "color": 0x2ECC71,
        "fields": [
            {"name": "SHA", "value": f"[`{sha}`]({url})", "inline": False},
            {"name": "Committer", "value": author_name, "inline": False},
            {"name": "Message", "value": msg, "inline": False},
            {"name": "Time (WIB)", "value": time_wib, "inline": False},
        ],
        "thumbnail": {"url": avatar}
    }

    return embed

def format_issues_embed(payload: dict) -> dict:
    repo = payload["repository"]["full_name"]
    action = payload["action"]
    issue = payload["issue"]
    title = issue["title"]
    url = issue["html_url"]
    user = issue["user"]["login"]

    embed = {
        "title": f"Issue {action} in {repo}",
        "color": 0x3498DB,
        "fields": [
            {"name": "Title", "value": f"[{title}]({url})", "inline": False},
            {"name": "User", "value": user, "inline": False},
        ]
    }
    return embed

def format_pr_embed(payload: dict) -> dict:
    repo = payload["repository"]["full_name"]
    action = payload["action"]
    pr = payload["pull_request"]
    title = pr["title"]
    url = pr["html_url"]
    user = pr["user"]["login"]

    embed = {
        "title": f"Pull Request {action} in {repo}",
        "color": 0x9B59B6,
        "fields": [
            {"name": "Title", "value": f"[{title}]({url})", "inline": False},
            {"name": "User", "value": user, "inline": False},
        ]
    }
    return embed

def format_create_embed(payload: dict) -> dict:
    repo = payload["repository"]["full_name"]
    ref = payload["ref"]
    ref_type = payload["ref_type"]  # "branch" or "tag"

    embed = {
        "title": f"Created {ref_type} in {repo}",
        "color": 0x2ECC71,
        "fields": [
            {"name": ref_type.title(), "value": ref, "inline": False},
        ]
    }
    return embed

def format_delete_embed(payload: dict) -> dict:
    repo = payload["repository"]["full_name"]
    ref = payload["ref"]
    ref_type = payload["ref_type"]

    embed = {
        "title": f"Deleted {ref_type} in {repo}",
        "color": 0xE74C3C,
        "fields": [
            {"name": ref_type.title(), "value": ref, "inline": False},
        ]
    }
    return embed

def format_watch_embed(payload: dict) -> dict:
    repo = payload["repository"]["full_name"]
    user = payload["sender"]["login"]
    avatar = payload["sender"]["avatar_url"]

    embed = {
        "title": f"⭐ Starred {repo}",
        "color": 0xF1C40F,
        "fields": [
            {"name": "User", "value": user, "inline": False},
        ],
        "thumbnail": {"url": avatar}
    }
    return embed

# --------------- User Events ---------------
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
    
    state_key = f"last_event_id_{username}"
    last_id = get_state(state_key)

    if last_id is None:
        set_state(state_key, events[0]["id"])
        return []
    
    new_raw = []
    for ev in events:
        if ev.get("id") == last_id:
            break
        new_raw.append(ev)

    if not new_raw:
        return []
    
    new_raw.reverse()

    set_state(state_key, events[0]["id"])

    return [_format_event(ev) for ev in new_raw]
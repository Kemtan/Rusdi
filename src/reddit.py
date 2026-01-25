import sqlite3, json, re
from urllib.parse import urljoin
from pathlib import Path

import requests
from requests_doh import DNSOverHTTPSAdapter
from bs4 import BeautifulSoup

DB_PATH = "reddit.db"
BASE = "https://www.reddit.com"
COOKIE_PATH = (Path(__file__).parent.parent / "cookies.json").resolve()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# DoH session
session = requests.Session()
session.mount("https://", DNSOverHTTPSAdapter())
session.mount("http://", DNSOverHTTPSAdapter())

# Cookies (optional, into headers)
if COOKIE_PATH.exists():
    with open(COOKIE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cookie_pairs = []

    # Playwright storage_state style: {"cookies":[...], "origins":[...]}
    if isinstance(data, dict) and isinstance(data.get("cookies"), list):
        for c in data["cookies"]:
            if isinstance(c, dict) and "name" in c and "value" in c:
                cookie_pairs.append(f"{c['name']}={c['value']}")

    # Simple mapping: {"name":"value", ...}
    elif isinstance(data, dict):
        for k, v in data.items():
            cookie_pairs.append(f"{k}={v}")

    # List style: [{"name":"..","value":".."}, ...]  OR  ["a=b", "c=d"]
    elif isinstance(data, list):
        for c in data:
            if isinstance(c, dict) and "name" in c and "value" in c:
                cookie_pairs.append(f"{c['name']}={c['value']}")
            elif isinstance(c, str) and "=" in c:
                cookie_pairs.append(c)

    if cookie_pairs:
        HEADERS["Cookie"] = "; ".join(cookie_pairs)
        print("cookies loaded into headers")
    else:
        print("cookies file found, but format not recognized / empty")
else:
    print("no cookies, running anonymous")

# DB
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")
conn.commit()

def get_last_seen_id(key: str):
    row = cur.execute("SELECT value FROM state WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None

def set_last_seen_id(key: str, value: str):
    cur.execute(
        "INSERT INTO state(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value)
    )
    conn.commit()

def fetch_user_posts(subreddit: str, username: str, limit=10):
    url = (
        f"{BASE}/r/{subreddit}/search/"
        f"?q=author:{username}&restrict_sr=1&sort=new&type=link"
    )

    posts = []

    while url and len(posts) < limit:
        try:
            resp = session.get(url, headers=HEADERS, timeout=20)
        except Exception as e:
            print("Request error:", e)
            break

        if resp.status_code != 200:
            print("HTTP", resp.status_code, url)
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Only get titles
        titles = soup.select("a[data-testid='post-title']")

        for title_el in titles:
            title = title_el.get_text(strip=True)
            link = urljoin(BASE, title_el["href"])
            parts = link.split("/")

            # Extract post_id from URL
            post_id = None
            if "comments" in parts:
                idx = parts.index("comments")
                if idx + 1 < len(parts):
                    post_id = parts[idx + 1]

            posts.append({
                "id": post_id,
                "title": title,
                "url": link,
                "author": username,
            })

            if len(posts) >= limit:
                break

        bar = soup.select_one(".pdp-credit-bar span[class^='avatar']")
        subimage = bar.find("img") if bar else None
        posts.append({"subimage": subimage})

        next_btn = soup.find("a", rel="nofollow next")
        url = next_btn["href"] if next_btn else None

    return posts

def check_new_posts(subreddit: str, username: str, limit=10):
    key = f"{subreddit}:{username}"
    last_seen = get_last_seen_id(key)

    posts = fetch_user_posts(subreddit, username, limit=limit)
    if not posts:
        return []

    new = []
    for post in posts:
        if post["id"] == last_seen:
            break
        new.append(post)

    if posts[0]["id"]:
        set_last_seen_id(key, posts[0]["id"])

    return list(reversed(new))



def fetch_user_comments(subreddit: str, username: str, limit=10):
    url = (
        f"{BASE}/r/{subreddit}/search/"
        f"?q=author:{username}&restrict_sr=1&sort=new&type=comment"
    )

    comments = []

    while url and len(comments) < limit:
        try:
            resp = session.get(url, headers=HEADERS, timeout=20)
        except Exception as e:
            print("Request error:", e)
            break

        if resp.status_code != 200:
            print("HTTP", resp.status_code, url)
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Comment bodies (matches: id="search-comment-...-rtjson-content")
        body_divs = soup.select("div[id^='search-comment-'][id$='-rtjson-content']")
        # Fallback (your sample shows the body nested under a span with id="comment-content-...")
        if not body_divs:
            body_divs = soup.select("span[id^='comment-content-'] div")

        for body_div in body_divs:
            body_text = body_div.get_text("\n", strip=True)
            if not body_text:
                continue

            # Try to find the permalink near this body
            # Usually there's an <a href="/r/.../comments/.../comment_id/"> close by
            a = body_div.find_parent("a", href=True)
            if a is None:
                a = body_div.find_previous("a", href=True) or body_div.find_next("a", href=True)

            link = urljoin(BASE, a["href"]) if a and a.get("href") else None

            # Extract comment_id from either the body_div id or the link
            comment_id = None
            m = re.search(r"\bt1_([A-Za-z0-9]+)\b", body_div.get("id", ""))
            if m:
                comment_id = m.group(1)
            elif link:
                m2 = re.search(r"/comments/[^/]+/[^/]+/([A-Za-z0-9]+)/", link)
                if m2:
                    comment_id = m2.group(1)

            comments.append({
                "id": comment_id,
                "body": body_text,
                "url": link,
                "author": username,
            })

            if len(comments) >= limit:
                break

        next_btn = soup.find("a", rel="nofollow next")
        url = next_btn["href"] if next_btn else None

    return comments

def check_new_comments(subreddit: str, username: str, limit=10):
    key = f"{subreddit}:{username}:comments"
    last_seen = get_last_seen_id(key)

    comments = fetch_user_comments(subreddit, username, limit=limit)
    if not comments:
        return []

    new = []
    for c in comments:
        if c["id"] == last_seen:
            break
        new.append(c)

    if comments[0].get("id"):
        set_last_seen_id(key, comments[0]["id"])

    return list(reversed(new))
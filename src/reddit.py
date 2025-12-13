import sqlite3
from urllib.parse import urljoin

import requests
from requests_doh import DNSOverHTTPSAdapter
from bs4 import BeautifulSoup

DB_PATH = "reddit.db"
BASE = "https://www.reddit.com"

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
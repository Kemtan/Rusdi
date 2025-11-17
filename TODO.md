# Todo
- [x] Base bot
- [x] Utils (ping, etc)
- [ ] github commits, issues, and PR logger (WIP)
- [ ] reddit post sender 

## Goal
- Bot runs 24/7
- Every hour:
  - Fetch latest Reddit post or GitHub commit
  - If it’s new → send to a specific channel
  - If not → do nothing
- Support basic commands like `!ping`

## 1. Project Setup
- Create folder, e.g. `Rusdi/`
- Inside, create:
  - `src/main.py`
  - `src/reddit_client.py`
  - `src/github_client.py`
  - `.env`
- Install dependencies:
  - `pip install discord.py python-dotenv requests`

## 2. .env File
```
DISCORD_TOKEN=your_discord_bot_token_here
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=yyy
REDDIT_USER_AGENT=RusdiBot/0.1 by yourname
GITHUB_TOKEN=ghp_...
```

## 3. Base Bot (main.py)
Set up:
- load dotenv
- bot intents
- basic commands
- channel ID
- hourly task loop

## 4. Data Source Clients
### Reddit (`reddit_client.py`)
Implement:
```
def fetch_latest_post(subreddit):
    return { "id": ..., "title": ..., "url": ... }
```

### GitHub (`github_client.py`)
Implement:
```
def fetch_latest_commit(owner, repo):
    return { "sha": ..., "message": ..., "url": ... }
```

## 5. Tracking Last Item
Use:
```
last_reddit_id = None
last_commit_sha = None
```

## 6. Hourly Loop
Example:
```
@tasks.loop(minutes=60)
async def hourly_check():
    latest = fetch_latest_post("memes")
    if latest["id"] != last_reddit_id:
        send to channel
        update last_reddit_id
```

## 7. Testing
Change to:
```
@tasks.loop(minutes=1)
```
for testing.

## 8. Later Improvements
- save last IDs into file/db
- better error handling
- manual trigger commands
- move features into cogs

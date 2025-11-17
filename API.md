# API Endpoints Cheat Sheet for Discord Bot

This file lists only the endpoints needed for Reddit + GitHub hourly checkers.

---

# 1. GitHub API (REST v3)

Docs:  
https://docs.github.com/en/rest

## A. Latest Commits
```
GET /repos/{owner}/{repo}/commits
```

Example:
```
https://api.github.com/repos/torvalds/linux/commits?per_page=1
```

Response (shape):
```json
[
  {
    "sha": "abc123",
    "commit": { "message": "Fix bug..." },
    "html_url": "https://github.com/torvalds/linux/commit/abc123"
  }
]
```

## B. Latest Release (optional)
```
GET /repos/{owner}/{repo}/releases/latest
```

Docs:  
https://docs.github.com/en/rest/releases/releases#get-the-latest-release

---

# 2. Reddit API (Official)

Docs:  
https://www.reddit.com/dev/api/

## A. Latest Posts
```
GET /r/{subreddit}/new.json?limit=1
```

Example:
```
https://www.reddit.com/r/memes/new.json?limit=1
```

Response (shape):
```json
{
  "data": {
    "children": [
      {
        "data": {
          "id": "abc123",
          "title": "Funny meme",
          "url": "https://i.redd.it/image.png",
          "permalink": "/r/memes/comments/abc123/title"
        }
      }
    ]
  }
}
```

## B. Top Posts of the Day
```
GET /r/{subreddit}/top.json?t=day&limit=1
```

## C. OAuth Token Endpoint
```
POST https://www.reddit.com/api/v1/access_token
```

Docs:  
https://www.reddit.com/dev/api/#POST_api_v1_access_token

Notes:
- Reddit requires OAuth + custom User-Agent.
- GitHub free up to 5k req/hr.
- One fetch/hour is extremely safe for both APIs.

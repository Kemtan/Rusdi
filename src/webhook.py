from aiohttp import web, ClientSession
import config
import github

API_BASE = "https://discord.com/api/v10"


async def send_embed_as_bot(embed: dict):
    url = f"{API_BASE}/channels/{config.CHANNEL_ID}/messages"
    headers = {
        "Authorization": f"Bot {config.DISCORD_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"embeds": [embed]}

    async with ClientSession() as session:
        resp = await session.post(url, headers=headers, json=payload)
        print("Discord bot status:", resp.status)
        if resp.status not in (200, 201):
            print("Discord error:", await resp.text())

async def github_webhook(request: web.Request):
    try:
        body = await request.json()
    except:
        return web.Response(status=400, text="bad payload\n")

    event = request.headers.get("X-GitHub-Event", "unknown")
    print("== Incoming GitHub webhook ==", event)

    if event != "push":
        return web.Response(text="ignored\n")

    embed = github.format_push_embed(body)
    if embed is None:
        return web.Response(text="invalid push\n")

    await send_embed_as_bot(embed)
    return web.Response(text="OK\n")

async def ok(request):
    return web.Response(text="Webhook server is running\n")

def create_app():
    app = web.Application()
    app.router.add_get("/github/webhook", ok)
    app.router.add_post("/github/webhook", github_webhook)
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8000)
from aiohttp import web, ClientSession
import config

async def send_to_discord(text: str):
    async with ClientSession() as session:
        await session.post(
            config.DISCORD_WEBHOOK_URL,
            json={"content": text},
        )

async def github_webhook(request: web.Request):
    body = await request.json()
    event = request.headers.get("X-GitHub-Event", "unknown")

    repo = body.get("repository", {}).get("full_name", "unknown/repo")

    msg = f"GitHub `{event}` event in `{repo}`"

    await send_to_discord(msg)

    return web.Response(text="OK")

def create_app():
    app = web.Application()
    app.router.add_post("/github/webhook", github_webhook)
    app.router.add_get("/github/webhook", lambda r: web.Response(text="Webhook OK"))  # for browser test
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8000)
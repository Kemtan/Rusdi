from playwright.sync_api import sync_playwright

TRR_URI = "https://cloudflare-dns.com/dns-query"

with sync_playwright() as p:
    context = p.firefox.launch_persistent_context(
        user_data_dir="pw_firefox_profile",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
        firefox_user_prefs={
            # DoH / TRR
            "network.trr.mode": 3,
            "network.trr.uri": TRR_URI,
            "network.trr.bootstrapAddress": "1.1.1.1",
            "network.dns.disableIPv6": True,
        },
    )

    page = context.new_page()
    page.goto("https://www.reddit.com/", wait_until="domcontentloaded")

    # login
    page.goto("https://www.reddit.com/login", wait_until="domcontentloaded")
    page.wait_for_timeout(60_000)

    # Export cookies
    context.storage_state(path="cookies.json")
    context.close()

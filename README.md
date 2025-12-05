# Rusdi
personal discord bot

# Features
- Log all github events to discord (webhook)
- aiohttp webhook server
- ping
- TBA. (see TODO.md)

# Project Structure
```├── LICENSE
├── README.md
├── requirements.txt
├── src
│   ├── config.py
│   ├── github.py
│   ├── main.py
│   ├── __pycache__
│   ├── utils.py
│   └── webhook.py
└── TODO.md
```

# Requirements
- Discord bot (your own token, etc.)
- Tailscale
    ```
    sudo pacman -S tailscale
    ```
- Python:
    - aiohttp 3.13.2
    - discord.py 2.6.4
    - dotenv 0.9.9

# Installation
```bash
python -m venv venv
pip install -r requirements.txt
source venv/bin/activate
```

```bash
cp .env.example .env
```
fill the .env based on your own preference.

# Running the Bot
main bot:
```bash
python3 src/main.py
```

webhook server:
```bash
python3 src/webhook.py
```

# Setup Tailscale
1. Open the [DNS](https://login.tailscale.com/admin/dns) page of the admin console.
2. Enable [MagicDNS](https://tailscale.com/kb/1081/magicdns#enabling-magicdns) if not already enabled for your tailnet.
3. Under **HTTPS Certificates**, select **Enable HTTPS**.
4. Acknowledge that your machine names and your tailnet DNS name will be published on a public ledger.
5. For each machine you are provisioning with a TLS certificate, run `tailscale cert` on the machine to obtain a certificate.
6. ```sudo tailscale funnel 8000```
7. ```curl -v https://<your-tailscale-url>/github/webhook``` should return ok

# Webhook Setup
1. Go to GitHub > Repo Settings > Webhooks
2. Set Payload URL to:  
```https://<your-tailscale-url>/github/webhook```
3. Choose Push events or Send me everything
4. Add a secret (optional but recommended)
5. Save     
(screenshots examples here)

# Discord Output
(image)

# Security Notes
- keep tokens private
- treat webhook URL as secrets
- don't leak .env

# Notes
MIT License.    
feel free to contribute and send PR, make sure to follow my commit style, thanks... 

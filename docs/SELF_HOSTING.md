# Self-Hosting AutoViralAI

This guide takes you from a fresh fork to an agent that posts to **your** Threads account 3x/day, with approvals in **your** Telegram.

Want to try it first without any accounts? Use the [Quick Start](../README.md#-quick-start) — it runs the full pipeline on mock APIs with only an Anthropic key.

## What you need

| Item | Why | Cost |
|---|---|---|
| Server with Docker + Docker Compose | Runs the agent and Postgres 24/7 | Any small VPS (1 GB RAM is enough) |
| Domain/subdomain with HTTPS | Telegram only delivers webhooks to public HTTPS URLs | Free with Caddy / Let's Encrypt |
| Anthropic API key | All LLM steps | Pay per use |
| Telegram bot | Approve / reject / edit posts | Free |
| Threads account + Meta developer app | Publishing and engagement metrics | Free |
| Apify account | Scraping viral Threads posts for research | Free tier, then pay per use |

## 1. Collect the keys

Copy the template first:

```bash
cp .env.example .env
```

### Anthropic

Create a key at <https://console.anthropic.com/> → `ANTHROPIC_API_KEY`.

### Telegram

1. Talk to [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token → `TELEGRAM_BOT_TOKEN`.
2. Send any message to your new bot, then get your chat ID:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"   # getUpdates doesn't work while a webhook is set
   curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
   ```
   Copy `result[0].message.chat.id` → `TELEGRAM_CHAT_ID`. Only this chat can control the agent.
3. Generate a webhook secret → `TELEGRAM_WEBHOOK_SECRET`:
   ```bash
   openssl rand -hex 32
   ```
4. Set `TELEGRAM_WEBHOOK_URL` to the public HTTPS base URL of your server, e.g. `https://agent.example.com`. The agent registers the webhook at `<url>/webhook/telegram` on startup.

### Threads

1. Create an app at <https://developers.facebook.com/apps/> with the **Access the Threads API** use case.
2. In the use case, enable permissions: `threads_basic`, `threads_content_publish`, `threads_manage_insights`.
3. Under **App roles → Roles**, add your Threads account as a **Threads Tester**, then accept the invite in the Threads app (Settings → Account → Website permissions → Invites).
4. Generate a user token for that account (Threads use case → Settings → User Token Generator).
5. Make sure the token is **long-lived** (60 days). If you got a short-lived one, exchange it:
   ```bash
   curl "https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=<APP_SECRET>&access_token=<SHORT_LIVED_TOKEN>"
   ```
   → `THREADS_ACCESS_TOKEN`. The agent refreshes it every Sunday and stores the new one in Postgres; if a refresh fails, you get a Telegram message.
6. Get your user ID → `THREADS_USER_ID`:
   ```bash
   curl "https://graph.threads.net/v1.0/me?fields=id,username&access_token=<TOKEN>"
   ```

### Apify

Copy your token from <https://console.apify.com/account/integrations> → `APIFY_API_TOKEN`. The agent calls the `burbn/threads-search-scraper` actor during research; check its pricing in the Apify store.

### Postgres and API

- Set `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (pick a strong password).
- Optional: `API_SECRET_KEY` protects the `/api/*` endpoints (send it as `X-API-Key`).

The agent refuses to start in production if any required value is missing, and the error lists which ones.

## 2. Make it yours

Edit `config/account_niche.yaml` (niche, voice, audience, content pillars, topics to avoid, hashtags) **before the first start**.

> The YAML is copied into Postgres on first boot only. After that, change settings with `/config` in Telegram, or reset the `pgdata` volume to re-read the YAML.

Posting schedule: creation runs at 08:00, 12:00 and 18:00, learning at 06:00 (Europe/Warsaw). To change this, edit `setup_schedules()` in `src/orchestrator.py`.

## 3. Deploy

### Option A: manually on the server

```bash
git clone https://github.com/<you>/AutoViralAI.git && cd AutoViralAI
cp .env.example .env   # fill it in (step 1)
docker build -t autoviralai:latest .
docker compose -f docker-compose.prod.yml up -d
```

`docker-compose.prod.yml` binds the agent to `127.0.0.1:8000`, so put an HTTPS reverse proxy in front. With [Caddy](https://caddyserver.com/docs/install), `/etc/caddy/Caddyfile`:

```
agent.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Then `systemctl reload caddy`. Caddy gets the certificate automatically once DNS points at the server.

To update: `git pull && docker build -t autoviralai:latest . && docker compose -f docker-compose.prod.yml up -d`.

### Option B: auto-deploy from GitHub Actions

Every push to `main` runs lint + tests, then builds the image and deploys it over SSH.

1. In `.github/workflows/ci.yml`, change the `deploy` job's `if: github.repository == 'kgarbacinski/AutoViralAI'` to your fork's name.
2. In your fork: **Settings → Secrets and variables → Actions**:
   - Secrets: `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_PRIVATE_KEY`, `HEALTH_CHECK_URL` (e.g. `https://agent.example.com/health`)
   - Variable: `REMOTE_DIR` (e.g. `/root/autoviralai`)
3. Upload your secrets once (and again whenever they change):
   ```bash
   SSH_HOST=your.server.com SSH_USER=root SSH_PORT=22 ./deploy.sh
   ```
4. Set up the reverse proxy from Option A on the server.
5. Push to `main`.

### Running the full stack locally

`docker compose up -d` (the root `docker-compose.yml`) builds the image and starts Postgres, but it also runs in production mode, so it needs every key above and a public HTTPS URL. For local tests, expose port 8000 with a tunnel (`cloudflared tunnel --url http://localhost:8000` or `ngrok http 8000`) and use that URL as `TELEGRAM_WEBHOOK_URL`.

## 4. Check that it works

1. `curl https://agent.example.com/health` → `{"status":"ok"}`
2. `docker compose -f docker-compose.prod.yml logs agent | grep -E "webhook set|fully started"` shows both lines.
3. In Telegram, send `/status` to the bot. It should reply with the agent state and the next run.
4. Send `/force` to run a creation cycle now. Within a few minutes you get the pipeline report and an approval message.
5. Approve it and check that the post appears on Threads.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Container exits with `Missing required production secrets: ...` | Fill in the listed variables in `.env` |
| Bot doesn't respond at all | Webhook not reachable: check HTTPS, the proxy, and `TELEGRAM_WEBHOOK_URL`. `curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"` shows the last delivery error |
| Bot only answers `/start` and `/help` | `TELEGRAM_CHAT_ID` is missing or isn't your chat |
| Publishing fails with 190 / OAuthException | Threads token expired: generate a new long-lived token, update `.env`, restart |
| Research finds nothing from Threads | Check `APIFY_API_TOKEN` and your Apify credit |
| `/api/*` returns 503 | `API_SECRET_KEY` isn't set |

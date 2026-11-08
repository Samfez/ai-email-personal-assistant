# AI Email Personal Assistant

An AI assistant for email and calendar work. It receives new messages in real time,
turns them into typed data, and (as it grows) classifies them, extracts what matters,
and proposes next steps such as reply drafts or calendar slots.

**The user stays in control.** The assistant proposes; it never sends, replies, deletes,
or changes a calendar event without explicit approval.

> **Status:** early development. Real-time inbound email capture is working end to end,
> and structured LLM output has been validated in standalone experiments. Classification
> and drafting are next. See [Roadmap](#roadmap).

## How it works

```
New email ─▶ Nylas ─▶ signed webhook (HTTPS) ─▶ cloudflared tunnel ─▶ FastAPI /events
                                                                         │
                                       verify HMAC signature (401 on mismatch)
                                       validate payload with Pydantic
                                       store raw event as JSON (gitignored)
                                                                         │
                                                                         ▼
                                                     GET /  →  list of captured messages
```

- **Nylas** provides one API over Gmail, Outlook, and other providers, handles OAuth, and
  pushes events through webhooks, so the app never polls the mailbox.
- **Webhook security:** every `POST /events` is verified against the `X-Nylas-Signature`
  HMAC with a constant-time comparison before the body is trusted. Nylas's `challenge`
  handshake is answered on `GET /events` when the webhook is registered.
- **Typed boundary:** incoming payloads are parsed into Pydantic models
  (`WebhookEvent` → `EmailObject`) at the edge, so the rest of the code works with
  validated data.
- **LLM layer (in progress):** OpenAI's Responses API with structured output parsed
  directly into Pydantic models. No free-text parsing.

## Tech stack

| Area             | Choice                                       |
| ---------------- | -------------------------------------------- |
| Language         | Python 3.12                                  |
| Package manager  | [uv](https://docs.astral.sh/uv/)             |
| API              | FastAPI + Uvicorn                            |
| Data models      | Pydantic v2                                  |
| Email & calendar | [Nylas API v3](https://developer.nylas.com/) |
| LLM              | OpenAI API                                   |
| Local tunnel     | Cloudflare Tunnel (`cloudflared`)            |
| Containers       | Docker Compose                               |

## Project structure

```
├── app/
│   ├── main.py                  # FastAPI app: webhook intake + captured-mail page
│   ├── config/
│   │   ├── config_auth.py       # one-time OAuth helper to obtain a Nylas grant ID
│   │   └── config_webhook.py    # registers the message.created webhook with Nylas
│   ├── schemas/                 # Pydantic models for webhook events and emails
│   └── templates/index.html     # minimal view of received messages
├── week2/                       # LLM experiments: Responses API, structured output
├── docker-compose.yml           # container smoke test (database service comes next)
├── .env.example                 # required configuration names, no values
└── pyproject.toml
```

## Getting started

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- A [Nylas](https://www.nylas.com/) account with an application and API key
- [`cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
  (`brew install cloudflared` on macOS)
- An OpenAI API key with credits, for the LLM experiments

A dedicated test mailbox is recommended: the assistant reads real message content.

### 1. Install and configure

```bash
uv sync
cp .env.example .env    # fill in your values; .env is gitignored
```

In the Nylas dashboard, add `http://localhost:5010/oauth/exchange` as a callback URI.

### 2. Connect a mailbox (one time)

```bash
cd app/config
uv run config_auth.py
```

Open `http://localhost:5010/nylas/auth`, sign in, and copy the returned grant ID into
`.env` as `NYLAS_GRANT_ID`. Stop the helper afterwards.

### 3. Run the server and expose it

```bash
# terminal 1
cd app
uv run main.py                                   # http://localhost:8000

# terminal 2
cloudflared tunnel --url http://localhost:8000   # prints a public https URL
```

Set `SERVER_URL` in `.env` to the tunnel URL (no trailing slash).

### 4. Register the webhook

```bash
# terminal 3
cd app/config
uv run config_webhook.py
```

The script prints a webhook secret. Save it as `WEBHOOK_SECRET` in `.env`, then restart
`main.py` so it picks up the new value.

### 5. Try it

Send an email to the connected mailbox. The server logs `POST /events 200`, the message
appears at `http://localhost:8000`, and the raw event is saved under `requests/events/`.

> Quick tunnels get a new URL on every restart. When that happens, update `SERVER_URL`,
> delete the old webhook in the Nylas dashboard, and register a new one.

### LLM experiments

```bash
uv run week2/openai-quickstart.py    # basic Responses API call
uv run week2/structured_output.py    # typed extraction into a Pydantic model
```

See [week2/README.md](week2/README.md) for details.

## Security & privacy

- Credentials live only in `.env`, which is never committed. `.env.example` lists the
  variable names with no values.
- Captured events contain real email content and are excluded from Git
  (`requests/events/*.json`).
- Any action with an external side effect (send, reply, delete, calendar changes) will be
  split into a draft step and an execute step that requires explicit approval.

## Roadmap

- [x] Project foundation: uv, Docker Compose, configuration contract
- [x] Real-time email capture: Nylas OAuth, signed webhooks, typed payloads
- [x] LLM groundwork: OpenAI structured output into Pydantic models
- [ ] Triage: classify inbound mail (needs reply, informational, scheduling, noise)
- [ ] Extraction & summaries: dates, tasks, and contacts from threads
- [ ] Reply drafts with an approval step before sending
- [ ] Calendar proposals: detect scheduling intent, suggest slots, confirm
- [ ] PostgreSQL persistence and idempotent event handling
- [ ] Deployment

### Current limitations

- Captured messages are held in memory and are lost when the server restarts.
- Duplicate webhook deliveries are not deduplicated yet.
- Run `main.py` from `app/`: template and schema paths are relative to that directory.

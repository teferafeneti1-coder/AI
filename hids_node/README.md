# HIDS Node

Subscribes to the Analysis Server's alert stream, shows the admin dashboard, and dispatches authenticated response commands to the Agent Node.

## Standalone Run

```bash
pip install -r requirements.txt
python ../proto/generate.py
cp .env.example .env
# Edit GRPC_SERVER_HOST and AGENT_HOST
python app.py
# Dashboard: http://localhost:5000
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GRPC_SERVER_HOST` | `localhost` | Analysis server IP |
| `GRPC_SERVER_PORT` | `50051` | Analysis server port |
| `AGENT_HOST` | `localhost` | Agent node IP |
| `AGENT_PORT` | `50052` | Agent node port |
| `WEB_HOST` | `0.0.0.0` | Flask bind address |
| `WEB_PORT` | `5000` | Flask port |
| `HMAC_SECRET` | `dev-secret-change-in-prod` | Must match agent's secret |
| `LOG_LEVEL` | `INFO` | Logging level |

## Dashboard Sections

- **System Status** — Normal / Warning / Under Attack (derived from recent alert severity)
- **Current Alert** — most recent alert with full details
- **Recommended Actions** — buttons that post to `/api/command` and dispatch signed gRPC commands
- **Alert History** — filterable table by severity / username

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Dashboard HTML |
| `GET` | `/api/alerts` | JSON alert history (query: severity, username, since) |
| `GET` | `/api/status` | Current system status |
| `POST` | `/api/command` | Send command to agent node |

# gRPC Analysis Server

Receives login event streams from the Audit Log Node, evaluates detection rules, and fans out alerts to all subscribed HIDS nodes.

## Standalone Run

```bash
pip install -r requirements.txt
# Generate stubs (from project root):
python ../proto/generate.py
# Configure:
cp .env.example .env
# Start:
python server.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GRPC_PORT` | `50051` | Port to listen on |
| `HMAC_SECRET` | `dev-secret-change-in-prod` | Shared HMAC secret |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DB_PATH` | `./alerts.db` | SQLite database path |

## Adding Detection Rules

Edit `rules.py`:
1. Write a function: `def rule_my_rule(events: list[LoginEvent]) -> Optional[dict]`
2. Return `_make_alert(...)` on match, or `None` if no match
3. Add it to `ALL_RULES` list at the bottom of the file

# Audit Log Service

Polls OS authentication logs and streams normalized events to the gRPC Analysis Server.

## Standalone Run

```bash
pip install -r requirements.txt
python ../proto/generate.py
cp .env.example .env
# Edit GRPC_SERVER_HOST to point at your Analysis Server IP
python service.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GRPC_SERVER_HOST` | `localhost` | Analysis server hostname/IP |
| `GRPC_SERVER_PORT` | `50051` | Analysis server gRPC port |
| `POLL_INTERVAL` | `5` | Seconds between log polls |
| `PLATFORM` | `auto` | `windows`, `linux`, `simulated`, or `auto` |
| `LOG_LEVEL` | `INFO` | Logging level |

## Platform Notes

- **Windows**: reads Security Event Log (events 4624/4625) via `pywin32`
- **Linux**: tails `/var/log/auth.log` for sshd Accepted/Failed lines
- **simulated**: generates synthetic events for demo/testing — no real OS access needed

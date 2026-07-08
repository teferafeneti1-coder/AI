# Agent Node

The monitored machine. Exposes a gRPC server that accepts authenticated commands from HIDS and executes them locally.

## Standalone Run

```bash
pip install -r requirements.txt
python ../proto/generate.py
cp .env.example .env
# Edit HMAC_SECRET to match HIDS and grpc_server
python agent.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_PORT` | `50052` | gRPC server port |
| `HMAC_SECRET` | `dev-secret-change-in-prod` | Shared HMAC secret |
| `LOG_LEVEL` | `INFO` | Logging level |

## Supported Commands

| Command Type | Windows | Linux | Description |
|--------------|---------|-------|-------------|
| `ignore` | ✅ | ✅ | No-op (acknowledge only) |
| `lock_account` | `net user <user> /active:no` | `passwd -l <user>` | Lock/disable user account |
| `stop_service` | `net stop <service>` | `systemctl stop <service>` | Stop a named service |
| `disconnect_network` | `Disable-NetAdapter` (PowerShell) | `ip link set <iface> down` | Disable all network adapters |
| `shutdown_device` | `shutdown /s /t 0` | `shutdown -h now` | Immediate shutdown |

## Security

- All commands require a valid HMAC-SHA256 signature with a ≤30s timestamp
- Commands older than 30s are rejected (replay protection)
- Failed signature checks are logged and rejected with a `CommandResult` error

## Privileges

- **Windows**: Run as Administrator for `net user`, `net stop`, `Disable-NetAdapter`, `shutdown`
- **Linux**: `sudo` is required for `passwd`, `systemctl`, `ip link set`, `shutdown` — ensure passwordless sudo or run the agent under a service account with the necessary capabilities

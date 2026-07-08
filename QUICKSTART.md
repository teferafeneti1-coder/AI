# HIDS — 5-Minute Quick Start

Get all four services running locally via Docker Compose, then see alerts in action.

## Prerequisites

- Docker + Docker Compose installed
- Python 3.11+ (for running the test harness)

## Steps

### 1️⃣ Generate proto stubs

```bash
# Install grpcio-tools (once)
py -m pip install grpcio-tools

# Generate stubs
py proto/generate.py
```

You should see:
```
Stubs generated in: proto/generated
Files:
  hids_pb2.py
  hids_pb2_grpc.py
  __init__.py
```

### 2️⃣ Start all services

```bash
docker-compose up --build
```

Wait for logs showing:
- `grpc_server_started` (gRPC Analysis Server on :50051)
- `agent_node_started` (Agent on :50052)
- `audit_log_service_started` (Audit log streaming)
- `hids_node_started` (Dashboard on :5000)

### 3️⃣ Open the dashboard

http://localhost:5000

You should see:
- System Status: **Normal**
- No active alerts yet

### 4️⃣ Simulate an attack

In a **new terminal**:

```bash
cd test_harness
py -m pip install grpcio protobuf
py simulate_attack.py --scenario all
```

Within seconds, you'll see:
- **CRITICAL** alert for credential stuffing (5 users from one IP)
- **HIGH** alert for brute force (7 failures on alice)
- **MEDIUM/HIGH** alert for IP sweep (12 failures from one IP)
- **LOW** alert for after-hours login

### 5️⃣ Try a response action

In the dashboard:
1. Click **Lock Account** → the agent will simulate locking the user
2. Check the agent logs: `docker logs hids_agent` — you'll see `command_executed` with `success=True` (in Docker, actual OS commands are no-ops, but in a real deployment they'd execute)

---

## Stopping

```bash
docker-compose down
```

## Troubleshooting

**Dashboard not loading?**
- Check `docker logs hids_node` for errors
- Ensure port 5000 is not in use

**No alerts appearing?**
- Check `docker logs hids_grpc_server` — rules may not be firing
- Check `docker logs hids_audit_log` — events should be streaming

**Commands not executing?**
- Verify `HMAC_SECRET` matches in `hids_node` and `agent_node` (set in docker-compose.yml)
- Check `docker logs hids_agent` for signature failures

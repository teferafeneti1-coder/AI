# Distributed HIDS — Host Intrusion Detection System

A four-service distributed HIDS built entirely in Python, communicating over gRPC + Protocol Buffers.

```
┌─────────────────┐     gRPC stream      ┌──────────────────────┐
│  Audit Log Node │ ──────────────────→  │  gRPC Analysis Server│
│  (auth events)  │                      │  (detection rules)    │
└─────────────────┘                      └──────────┬───────────┘
                                                     │ stream alerts
                                                     ▼
                                          ┌──────────────────────┐
                                          │   HIDS Node           │
                                          │   Flask dashboard     │◄── Admin browser
                                          └──────────┬───────────┘
                                                     │ ExecuteCommand RPC
                                                     ▼
                                          ┌──────────────────────┐
                                          │   Agent Node          │
                                          │   (monitored machine) │
                                          └──────────────────────┘
```

## Services

| Service | Entry Point | Default Port |
|---------|-------------|--------------|
| gRPC Analysis Server | `grpc_server/server.py` | 50051 |
| Audit Log Node | `audit_log_service/service.py` | — (client only) |
| HIDS Node + Dashboard | `hids_node/app.py` | 5000 (HTTP), connects to 50051 |
| Agent Node | `agent_node/agent.py` | 50052 |

---

## Quick Start — Docker Compose (all 4 on one machine)

```bash
# 1. From project root — generate proto stubs first
pip install grpcio-tools==1.64.1
python proto/generate.py

# 2. Start all services
docker-compose up --build

# 3. Open dashboard
http://localhost:5000

# 4. In a new terminal, run the attack simulator
cd test_harness
pip install grpcio==1.64.1 protobuf==5.27.2
python simulate_attack.py --scenario all
```

---

## Four-Machine Setup (Physical / VM)

Assign static IPs and note them:

| Machine | Role | IP Example |
|---------|------|------------|
| Machine A | gRPC Analysis Server | 192.168.1.10 |
| Machine B | Audit Log Node | 192.168.1.11 |
| Machine C | HIDS Node + Dashboard | 192.168.1.12 |
| Machine D | Agent Node (monitored) | 192.168.1.13 |

### Step 1 — Generate stubs (run once on any machine, copy to all)

```bash
pip install grpcio-tools==1.64.1
python proto/generate.py
# Copy proto/generated/ to each machine's service folder
```

### Step 2 — Machine A: gRPC Analysis Server

```bash
cd grpc_server
cp .env.example .env
# Edit .env — set HMAC_SECRET to a strong shared secret
pip install -r requirements.txt
python server.py
```

### Step 3 — Machine D: Agent Node

```bash
cd agent_node
cp .env.example .env
# Edit .env — same HMAC_SECRET as Machine A
pip install -r requirements.txt
python agent.py
```

### Step 4 — Machine C: HIDS Node

```bash
cd hids_node
cp .env.example .env
# Edit .env:
#   GRPC_SERVER_HOST=192.168.1.10
#   AGENT_HOST=192.168.1.13
#   HMAC_SECRET=<same secret>
pip install -r requirements.txt
python app.py
# Dashboard at http://192.168.1.12:5000
```

### Step 5 — Machine B: Audit Log Node

```bash
cd audit_log_service
cp .env.example .env
# Edit .env:
#   GRPC_SERVER_HOST=192.168.1.10
#   PLATFORM=auto   (auto-detects windows/linux)
pip install -r requirements.txt
python service.py
```

---

## Running the Attack Simulator

From any machine that can reach the gRPC Analysis Server:

```bash
cd test_harness
pip install grpcio==1.64.1 protobuf==5.27.2
python simulate_attack.py --host 192.168.1.10 --scenario all
```

Scenarios:
- `brute_force` — 7 failed logins for alice → HIGH alert
- `ip_sweep` — 12 failures from one IP → MEDIUM/HIGH alert
- `credential_stuffing` — failures across 5 usernames → CRITICAL alert
- `after_hours` — successful login at 3am → LOW alert
- `all` — runs all four sequentially

---

## Security Notes

- All inter-service commands are signed with HMAC-SHA256 (shared secret in `.env`)
- Commands older than 30 seconds are rejected (replay protection)
- The `HMAC_SECRET` must be identical on `grpc_server`, `hids_node`, and `agent_node`
- For production: replace HMAC with mutual TLS (`grpc.ssl_channel_credentials`)
- **Destructive commands** (Shutdown Device, Disconnect Network) require a confirmation modal in the dashboard before being sent

---

## Detection Rules

Rules live in `grpc_server/rules.py` — add new functions and register them in `ALL_RULES`:

| Rule | Trigger | Severity |
|------|---------|----------|
| `rule_brute_force` | ≥5 failures for same user in 2 min | HIGH |
| `rule_ip_sweep` | ≥10 failures from same IP in 2 min | MEDIUM/HIGH |
| `rule_credential_stuffing` | failures across ≥3 usernames from same IP | CRITICAL |
| `rule_after_hours_login` | successful login between 10pm–6am | LOW |

---

## Architecture Details

- **Streaming RPC**: Audit log → Analysis Server uses `SendLoginHistory(stream LoginRecord)` — events arrive in real time.
- **Fan-out subscription**: Multiple HIDS nodes can subscribe to `SubscribeAlerts` simultaneously via an in-memory broadcaster.
- **Retry/backoff**: Both the audit log sender and HIDS subscriber reconnect automatically with exponential backoff (max 60s).
- **Deduplication**: Identical alert types from the same source are suppressed for 30s.
- **Dashboard**: Flask + SocketIO push (`socket.emit('new_alert', ...)`) → live updates in the browser without polling.

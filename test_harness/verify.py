#!/usr/bin/env python3
"""
Quick local verification — tests proto stubs + detection rules without running any servers.
Run: py test_harness/verify.py
"""
import sys, os, time, uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto', 'generated'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'grpc_server'))

# 1. Proto stubs
import hids_pb2
import hids_pb2_grpc
print("[OK] Proto stubs imported")

# 2. Rules engine
import rules

now = time.time()
mk = lambda user, ip, status, ts=None: rules.LoginEvent(
    username=user, timestamp=ts or now,
    source_ip=ip, status=status,
    attempt_id=str(uuid.uuid4())
)

# Brute force
events = [mk('alice', '10.0.0.1', 'fail', now - i*5) for i in range(7)]
r = rules.rule_brute_force(events)
assert r and r['severity'] == 'HIGH', f"Expected HIGH, got {r}"
print(f"[OK] rule_brute_force → {r['severity']} / {r['attack_type']}")

# Credential stuffing
cs_events = [mk(f'user{i}', '9.9.9.9', 'fail') for i in range(5)] * 2
r = rules.rule_credential_stuffing(cs_events)
assert r and r['severity'] == 'CRITICAL', f"Expected CRITICAL, got {r}"
print(f"[OK] rule_credential_stuffing → {r['severity']} / {r['attack_type']}")

# IP sweep
sweep_events = [mk('bob', '1.2.3.4', 'fail') for _ in range(12)]
r = rules.rule_ip_sweep(sweep_events)
assert r and r['severity'] in ('MEDIUM', 'HIGH'), f"Expected MEDIUM/HIGH, got {r}"
print(f"[OK] rule_ip_sweep → {r['severity']} / {r['attack_type']}")

# After-hours login (3am)
import datetime
three_am = datetime.datetime.now().replace(hour=3, minute=0, second=0)
r = rules.rule_after_hours_login([mk('irene', '192.168.0.1', 'success', three_am.timestamp())])
assert r and r['severity'] == 'LOW', f"Expected LOW, got {r}"
print(f"[OK] rule_after_hours_login → {r['severity']} / {r['attack_type']}")

# 3. No-match case
no_events = [mk('bob', '10.0.0.2', 'success')]
r = rules.rule_brute_force(no_events)
assert r is None, "Should not fire on single success"
print("[OK] No false-positive on single success")

print("\nAll verifications passed.")

#!/usr/bin/env python3
"""
HIDS Test Harness — simulates various attack patterns against the gRPC Analysis Server.

Usage:
  python simulate_attack.py [--host HOST] [--port PORT] [--scenario SCENARIO]

Scenarios:
  brute_force          - 7 failed logins for 'alice' within 30s (triggers HIGH)
  ip_sweep             - 12 failures from one IP across 2 users (triggers MEDIUM/HIGH)
  credential_stuffing  - failures across 5 usernames from same IP (triggers CRITICAL)
  after_hours          - successful login at 3am timestamp (triggers LOW)
  all                  - run all scenarios sequentially
"""

import sys
import os
import time
import argparse
import uuid
import logging

import grpc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto", "generated"))
import hids_pb2
import hids_pb2_grpc

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("test_harness")


def make_record(username: str, source_ip: str, status: str,
                timestamp: float = None) -> hids_pb2.LoginRecord:
    return hids_pb2.LoginRecord(
        username=username,
        timestamp=int(timestamp or time.time()),
        source_ip=source_ip,
        status=status,
        attempt_id=str(uuid.uuid4()),
    )


def scenario_brute_force(stub) -> None:
    """7 failed logins for alice from same IP within seconds."""
    logger.info("=== Scenario: Brute Force (alice) ===")

    def gen():
        for i in range(7):
            rec = make_record("alice", "10.0.0.55", "fail")
            logger.info("  Sending failed login #%d for alice", i + 1)
            yield rec
            time.sleep(0.3)

    stub.SendLoginHistory(gen())
    logger.info("  Done — expect HIGH brute_force alert")


def scenario_ip_sweep(stub) -> None:
    """12 failures from one IP against 2 users."""
    logger.info("=== Scenario: IP Sweep (10.0.1.99) ===")

    def gen():
        for i in range(6):
            yield make_record("bob", "10.0.1.99", "fail")
            time.sleep(0.1)
        for i in range(6):
            yield make_record("charlie", "10.0.1.99", "fail")
            time.sleep(0.1)

    stub.SendLoginHistory(gen())
    logger.info("  Done — expect MEDIUM/HIGH ip_sweep alert")


def scenario_credential_stuffing(stub) -> None:
    """Failures across 5 different usernames from the same IP — critical threat."""
    logger.info("=== Scenario: Credential Stuffing (172.16.99.1) ===")
    users = ["dave", "eve", "frank", "grace", "henry"]

    def gen():
        for _ in range(2):
            for user in users:
                yield make_record(user, "172.16.99.1", "fail")
                time.sleep(0.1)

    stub.SendLoginHistory(gen())
    logger.info("  Done — expect CRITICAL credential_stuffing alert")


def scenario_after_hours(stub) -> None:
    """Successful login at 3am local time."""
    logger.info("=== Scenario: After Hours Login ===")
    import datetime
    # Set timestamp to 3:00 AM today
    now = datetime.datetime.now()
    three_am = now.replace(hour=3, minute=0, second=0, microsecond=0)
    ts = three_am.timestamp()

    def gen():
        yield make_record("irene", "192.168.0.200", "success", timestamp=ts)

    stub.SendLoginHistory(gen())
    logger.info("  Done — expect LOW after_hours_login alert")


def main():
    parser = argparse.ArgumentParser(description="HIDS attack simulator")
    parser.add_argument("--host", default="localhost", help="Analysis server host")
    parser.add_argument("--port", default=50051, type=int)
    parser.add_argument("--scenario",
                        choices=["brute_force", "ip_sweep",
                                 "credential_stuffing", "after_hours", "all"],
                        default="all")
    args = parser.parse_args()

    target = f"{args.host}:{args.port}"
    logger.info("Connecting to gRPC Analysis Server at %s", target)

    channel = grpc.insecure_channel(target)
    stub = hids_pb2_grpc.AnalysisServiceStub(channel)

    scenarios = {
        "brute_force": scenario_brute_force,
        "ip_sweep": scenario_ip_sweep,
        "credential_stuffing": scenario_credential_stuffing,
        "after_hours": scenario_after_hours,
    }

    if args.scenario == "all":
        for name, fn in scenarios.items():
            fn(stub)
            time.sleep(1)
    else:
        scenarios[args.scenario](stub)

    logger.info("Test harness complete. Check your HIDS dashboard for alerts.")
    channel.close()


if __name__ == "__main__":
    main()

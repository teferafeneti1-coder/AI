#!/usr/bin/env python3
"""
Generate Python gRPC stubs from proto/hids.proto.
Run from the project root: python proto/generate.py
Requires: grpcio-tools (pip install grpcio-tools)
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTO_DIR = os.path.join(ROOT, "proto")
OUT_DIR = os.path.join(PROTO_DIR, "generated")

os.makedirs(OUT_DIR, exist_ok=True)

# Write __init__.py so the package is importable
init = os.path.join(OUT_DIR, "__init__.py")
if not os.path.exists(init):
    open(init, "w").close()

cmd = [
    sys.executable, "-m", "grpc_tools.protoc",
    f"--proto_path={PROTO_DIR}",
    f"--python_out={OUT_DIR}",
    f"--grpc_python_out={OUT_DIR}",
    os.path.join(PROTO_DIR, "hids.proto"),
]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode != 0:
    print("ERROR:", result.stderr)
    sys.exit(1)

print("Stubs generated in:", OUT_DIR)
print("Files:")
for f in os.listdir(OUT_DIR):
    print(f"  {f}")

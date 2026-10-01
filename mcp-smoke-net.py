#!/usr/bin/env python3
"""MCP stdio client with working network config for the container."""
import json, subprocess, sys

CMD = ["podman", "run", "-i", "--rm", "--network=host",
       "-e", "no_proxy=localhost,127.0.0.1",
       "-e", "NO_PROXY=localhost,127.0.0.1",
       "-v", "/etc/ssl/certs/ca-certificates.crt:/tmp/ca.crt:ro",
       "-e", "SSL_CERT_FILE=/tmp/ca.crt",
       "localhost/amazon-mcp-server:latest"]
p = subprocess.Popen(CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)

def rpc(msg):
    p.stdin.write(json.dumps(msg) + "\n"); p.stdin.flush()
    line = p.stdout.readline()
    if not line:
        raise RuntimeError("server closed stdout")
    return json.loads(line)

def req(method, params=None, _id=1):
    m = {"jsonrpc": "2.0", "id": _id, "method": method}
    if params is not None: m["params"] = params
    return m

rid = 1
init = rpc(req("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "smoke-test", "version": "0.1"}}, _id=rid)); rid += 1
print("server:", init["result"]["serverInfo"]["name"])
p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"); p.stdin.flush()
tools = rpc(req("tools/list", {}, _id=rid)); rid += 1
print("tools:", [t["name"] for t in tools["result"]["tools"]])

name, args = sys.argv[1], json.loads(sys.argv[2] if len(sys.argv) > 2 else "{}")
res = rpc(req("tools/call", {"name": name, "arguments": args}, _id=rid))
text = res["result"]["content"][0]["text"]
print(f"--- {name} result (first 800 chars) ---")
print(text[:800])
p.stdin.close(); p.wait(timeout=120)
print("server exited cleanly")

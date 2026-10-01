#!/usr/bin/env python3
"""Minimal MCP stdio client: initialize, list tools, optionally call one."""
import json, subprocess, sys

CMD = ["podman", "run", "-i", "--rm", "--network=host", "localhost/amazon-mcp-server:latest"]
p = subprocess.Popen(CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)

def rpc(msg):
    p.stdin.write(json.dumps(msg) + "\n")
    p.stdin.flush()
    line = p.stdout.readline()
    if not line:
        raise RuntimeError("server closed stdout (see container stderr)")
    return json.loads(line)

def req(method, params=None, _id=1):
    m = {"jsonrpc": "2.0", "id": _id, "method": method}
    if params is not None:
        m["params"] = params
    return m

def note(method, params=None):
    m = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        m["params"] = params
    return m

rid = 1
init = rpc(req("initialize", {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "smoke-test", "version": "0.1"},
}, _id=rid)); rid += 1
print("server:", init.get("result", {}).get("serverInfo", {}).get("name"))
p.stdin.write(json.dumps(note("notifications/initialized")) + "\n"); p.stdin.flush()

tools = rpc(req("tools/list", {}, _id=rid)); rid += 1
names = [t["name"] for t in tools.get("result", {}).get("tools", [])]
print("tools:", names)

if len(sys.argv) > 1 and sys.argv[1] == "call":
    res = rpc(req("tools/call", {
        "name": "search_products",
        "arguments": {"query": "wireless headphones", "max_results": 2},
    }, _id=rid))
    print("tools/call result:", json.dumps(res)[:600])

p.stdin.close()
p.wait(timeout=120)
print("server exited cleanly")

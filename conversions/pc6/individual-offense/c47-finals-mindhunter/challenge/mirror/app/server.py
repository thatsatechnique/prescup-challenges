#!/usr/bin/env python3
"""
Mindhunter mirror server (CTF-NG port).

One parametrized Flask application drives all four "mirror" stages. The stage is
selected with the STAGE environment variable (1-4); the port with PORT. Each
stage exposes exactly one vulnerable endpoint and a randomly-selected set of
"magic" endpoints that must be visited before the vulnerability is armed.

VM->container substitutions applied here (see private/docs/architecture.md):
  * vmtoolsd guestinfo token retrieval -> token{1..4} environment variables.
  * Static ALLOWED_IPS whitelist -> live DNS resolution of the `perspective`
    jump host, so a request is only honoured when it arrives through the SOCKS
    pivot (its source address is perspective's address on the internal network).

The per-stage validation logic (headers, magic-endpoint gating, payload shapes,
timing window, sha224 command check) is preserved verbatim from the original
challenge servers.
"""

import base64
import hashlib
import json
import os
import random
import re
import socket
import sys
import threading
import time
from collections import defaultdict

from flask import Flask, jsonify, render_template, request, send_file

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

STAGE = int(os.environ.get("STAGE", "1"))
PORT = int(os.environ.get("PORT", str(5000 + STAGE)))

# Tokens are injected as environment variables (formerly vmtoolsd guestinfo).
TOKEN1 = os.environ.get("token1", "")
TOKEN2 = os.environ.get("token2", "")
TOKEN3 = os.environ.get("token3", "")
TOKEN4 = os.environ.get("token4", "")

# Host whose source address is permitted to reach the mirrors. In the original
# challenge this was the static IP of the `perspective` proxy VM (10.4.4.254).
# Here it is resolved live so it tracks the container's dynamic address.
PIVOT_HOST = os.environ.get("PIVOT_HOST", "perspective")

# How many magic endpoints each stage requires (mind/body/soul/peace).
MAGIC_COUNT = {1: 4, 2: 8, 3: 16, 4: 32}[STAGE]

visit_tracker = defaultdict(set)
global_trigger_map = {}

quotes = {
    "mind": "The mind is everything. What you think, you become.",
    "body": "Take care of your body. It's the only place you have to live.",
    "soul": "You don't have a soul. You are a soul. You have a body.",
    "peace": "Peace comes from within. Do not seek it without.",
}

# Endpoint pool the magic endpoints are sampled from (matches the originals).
extra_endpoints = [
    "admin", "login", "logout", "dashboard", "settings", "profile", "help", "config",
    "debug", "update", "upload", "download", "backup", "restore", "reset", "user",
    "data", "search", "report", "export", "import", "activity", "audit", "analytics",
    "cache", "queue", "worker", "jobs", "monitor", "logs", "notifications", "messages",
    "preferences", "security", "access", "permissions", "roles", "tokens", "sessions",
    "hooks", "events", "integrations", "webhooks", "sync", "database", "system",
    "support", "file", "admin_panel", "billing", "customer", "developer",
    "server_status", "payment", "checkout", "cart", "order", "subscription", "renew",
    "user_settings", "team", "workspace", "audit_log", "email", "verification",
]

required_magic = set(random.sample(extra_endpoints, MAGIC_COUNT))

# --------------------------------------------------------------------------- #
# Access control: only traffic that arrives through the pivot is honoured.
# --------------------------------------------------------------------------- #

_allowed_cache = {"ips": set(), "ts": 0.0}


def allowed_ips():
    """Resolve the pivot host's addresses (cached ~15s)."""
    now = time.time()
    if now - _allowed_cache["ts"] > 15 or not _allowed_cache["ips"]:
        ips = set()
        try:
            for info in socket.getaddrinfo(PIVOT_HOST, None):
                ips.add(info[4][0])
        except socket.gaierror:
            pass
        if ips:
            _allowed_cache["ips"] = ips
            _allowed_cache["ts"] = now
    return _allowed_cache["ips"]


def check_ip():
    return request.remote_addr in allowed_ips()


def get_resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def make_view(endpoint_name, inverted=False):
    """Generic magic-endpoint view. Visiting it records progress."""
    def view():
        client_ip = request.remote_addr
        visit_tracker[client_ip].add(endpoint_name)
        quote = quotes.get(endpoint_name, "Nothing is as it seems.")
        if inverted:
            # Peace stage: the "correct" endpoints report as forbidden (right is
            # wrong, wrong is right). Visit is still recorded above.
            return (
                f"<h1 style='color: black'>❌ You have found the /{endpoint_name} "
                f"perspective.</h1><p>{quote}</p>",
                403,
            )
        return (
            f"<h1 style='color: green'>✅ You have found the /{endpoint_name} "
            f"perspective.</h1><p>{quote}</p>",
            200,
        )
    view.__name__ = f"view_{endpoint_name}_{random.randint(1000, 9999)}"
    return view


# --------------------------------------------------------------------------- #
# Application factory
# --------------------------------------------------------------------------- #

def create_app():
    app = Flask(
        f"mirror{STAGE}",
        template_folder=get_resource_path("templates"),
        static_folder=get_resource_path("static"),
    )

    landing = {1: "landing1.html", 2: "landing2.html", 3: "landing3.html", 4: "landing4.html"}[STAGE]
    title = {1: "Mind Portal", 2: "Body Portal", 3: "Soul Portal", 4: "Peace Portal"}[STAGE]
    image = f"mirror{STAGE}.jpg"

    @app.route("/", endpoint="index")
    def index():
        return render_template(landing, title=title, image_file=image)

    @app.route("/explorer")
    def explorer():
        return render_template("explorer.html")

    def magic_ready():
        client_ip = request.remote_addr
        return required_magic.issubset(visit_tracker[client_ip])

    aspect = {1: "mind", 2: "body", 3: "soul", 4: "peace"}[STAGE]

    def not_ready():
        return jsonify({
            "error": "Not ready yet",
            "hint": f"\U0001f30e Your journey is incomplete. Explore more of your {aspect} before continuing.",
        }), 403

    # ------------------------------------------------------------------ #
    # Stage 1 - Mind - Server Side Request Forgery
    # ------------------------------------------------------------------ #
    if STAGE == 1:
        next_headers = {"X-Forwarded-Mind": TOKEN1, "X-Perspective": "resilience"}

        @app.route("/manual")
        def manual():
            # /manual records a visit like any other endpoint, then serves hints.
            visit_tracker[request.remote_addr].add("manual")
            return render_template("manual.html")

        @app.route("/fetch", methods=["GET"])
        def ssrf():
            if not magic_ready():
                return not_ready()
            if not check_ip():
                return jsonify({"error": "Unauthorized IP Detected."}), 403
            target = request.args.get("url")
            if not target:
                return jsonify({"error": "No URL provided"}), 400
            if re.match(r"^(http|https)://(localhost|127\.0\.0\.1|10\.1\.1|10\.2\.2|10\.3\.3)", target):
                return jsonify({"error": "Access Denied"}), 403
            try:
                import requests
                time.sleep(random.uniform(0.5, 2.0))
                requests.get(target, timeout=2)
                return jsonify({"next_headers": next_headers, "\U0001fa99 token 1": TOKEN1})
            except Exception as e:  # noqa: BLE001
                return jsonify({"error": str(e)})

    # ------------------------------------------------------------------ #
    # Stage 2 - Body - Prototype Pollution
    # ------------------------------------------------------------------ #
    elif STAGE == 2:
        required_headers = {"X-Forwarded-Mind": TOKEN1, "X-Perspective": "resilience"}
        next_headers = {"X-Forwarded-Mind": TOKEN1, "X-Forwarded-Body": TOKEN2, "X-Perspective": "awakened"}

        def check_headers():
            for key, value in required_headers.items():
                if request.headers.get(key) != value:
                    return False
            return True

        @app.route("/stop", methods=["POST"])
        def prototype_pollution():
            if not check_headers() or not check_ip() or not request.headers.get("X-Forwarded-Mind"):
                return jsonify({"error": "Unauthorized Access. Listen to your body - you have not met your true potential yet."}), 403
            if not magic_ready():
                return not_ready()

            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                return jsonify({"error": "Malformed structure."})

            if "meta" in data and isinstance(data["meta"], dict):
                proto_obj = data["meta"].get("__proto__")
                if proto_obj and isinstance(proto_obj, dict):
                    if "polluted" in proto_obj and proto_obj["polluted"] == "true":
                        return jsonify({"next_headers": next_headers, "\U0001fa99 token 2": TOKEN2})
                    return jsonify({
                        "error": "You've reached the prototype. But something is missing.",
                        "hint": "\U0001f309 All this smog; is it true that this world is 'polluted'. Set it.",
                    })
                if "__proto__" in data["meta"]:
                    return jsonify({"error": "You're close...", "hint": "Try using a dict instead of a string for __proto__"})
            elif "__proto__" in data:
                return jsonify({
                    "error": "Hmm. That doesn't quite reach the right prototype.",
                    "hint": "Try wrapping your prototype in a container... like 'meta'.",
                })
            return jsonify({"error": "This isn't the shape we were expecting. We're expecting nested activity."})

    # ------------------------------------------------------------------ #
    # Stage 3 - Soul - Encoded command / restricted write + download
    # ------------------------------------------------------------------ #
    elif STAGE == 3:
        required_headers = {
            "X-Forwarded-Mind": TOKEN1,
            "X-Forwarded-Body": TOKEN2,
            "X-Perspective": "awakened",
        }
        next_headers = {"X-Forwarded-Mind": TOKEN1, "X-Forwarded-Body": TOKEN2, "X-Perspective": "acceptance"}

        def check_headers():
            for key, value in required_headers.items():
                if request.headers.get(key) != value:
                    return False
            return True

        @app.route("/encode", methods=["POST"])
        def encode():
            if (not check_headers() or not check_ip()
                    or not request.headers.get("X-Forwarded-Mind")
                    or not request.headers.get("X-Forwarded-Body")):
                return jsonify({"error": "Unauthorized Access. Listen to your soul - you have not met your true potential yet."}), 403
            if not magic_ready():
                return not_ready()

            try:
                data = json.loads(request.data)
            except Exception:
                return jsonify({"error": "Malformed JSON", "hint": "Are you sending proper application/json?"}), 400
            try:
                task = data["task"]
            except (KeyError, TypeError):
                return jsonify({"error": "Improper structure.", "hint": "The journey begins at 'task'. Ensure your JSON has a 'task' object."}), 400
            if not isinstance(task, dict):
                return jsonify({"error": "Improper structure.", "hint": "Task must be a JSON object (not a string or number)."}), 400
            if "payload" not in task or "exec" not in task["payload"] or "cmd" not in task["payload"]["exec"]:
                return jsonify({"error": "Missing fields.", "hint": "Inside 'task', you must have 'payload' → 'exec' → 'cmd'."}), 400

            encoded_cmd = data["task"]["payload"]["exec"]["cmd"]
            try:
                decoded = base64.b64decode(encoded_cmd)
            except Exception:
                return jsonify({"error": "Failed to decode your command.", "hint": "Try base64 encoding your payload before sending it."}), 400

            expected_hash = [
                "3d43dd3e12f4bd70d1781c573287c36973ddad788ae2853f0b995928",
                "481896434a94e2dbbf53889a496c75aed716c86c337045b0036ef14d",
            ]
            digest = hashlib.sha224(decoded).hexdigest()
            if digest not in expected_hash:
                return jsonify({
                    "error": "Your command feels... hollow and without 'soul'.",
                    "hint": "The decoded result does not resonate. Seek balance in entropy.",
                }), 403

            if decoded.strip() == b"unlock":
                return jsonify({"status": "Command executed", "path": "/tmp/fake_success.log", "message": "All systems go (but not really). Try again."})

            os.makedirs("/tmp/restricted/", exist_ok=True)
            output_file = os.path.join("/tmp/restricted/", "token.txt")
            with open(output_file, "w") as f:
                f.write(f"\U0001fa99 token: {TOKEN3}, new header: 'X-Forwarded-Soul: {TOKEN3}' unlocked.")
            time.sleep(random.uniform(1.5, 3.5))
            return jsonify({
                "message": "\U0001f3af Command executed successfully in restricted environment.",
                "path": "Please GET the /download_token endpoint for your token",
                "next_headers": next_headers,
            })

        @app.route("/download_token", methods=["GET"])
        def download_token():
            output_file = "/tmp/restricted/token.txt"
            if not os.path.exists(output_file):
                return jsonify({"error": "Token not yet generated.", "hint": "Complete the soul challenge first."}), 404
            return send_file(output_file, as_attachment=True)

    # ------------------------------------------------------------------ #
    # Stage 4 - Peace - Race condition / timing window
    # ------------------------------------------------------------------ #
    elif STAGE == 4:
        required_headers = {
            "X-Forwarded-Mind": TOKEN1,
            "X-Forwarded-Body": TOKEN2,
            "X-Forwarded-Soul": TOKEN3,
            "X-Perspective": "acceptance",
        }

        def check_headers():
            for key, value in required_headers.items():
                if request.headers.get(key) != value:
                    return False
            return True

        @app.route("/timeout", methods=["PATCH"])
        def timeout():
            if (not check_headers() or not check_ip()
                    or not request.headers.get("X-Forwarded-Mind")
                    or not request.headers.get("X-Forwarded-Body")
                    or not request.headers.get("X-Forwarded-Soul")):
                return jsonify({"error": "Unauthorized Access. Listen to your soul - you have not met your true potential yet."}), 403
            if not magic_ready():
                return not_ready()

            client_ip = request.remote_addr
            now = time.time()
            timestamps = global_trigger_map.get(client_ip, [])
            timestamps.append(now)
            global_trigger_map[client_ip] = timestamps

            if len(timestamps) == 2:
                first, second = timestamps
                delta = second - first
                del global_trigger_map[client_ip]
                # Window widened slightly from the original 9.5-10.5s to absorb
                # SOCKS-pivot jitter; competitor still targets a ~10s cadence.
                if 8.5 <= delta <= 12.0:
                    return jsonify({
                        "\U0001fa99 token": TOKEN4,
                        "message": "\U0001f33f You achieved peace by mastering the flow of time.",
                    })
                return jsonify({
                    "error": "Your timing was off. It takes anywhere from a second to a minute to change your left.",
                    "hint": " You are in a \U0001f3af race with yourself, mindhunter.",
                })
            return jsonify({"message": "First move recorded. Breathe deeply. Repeat this move but guess when you must take it."})

    # ------------------------------------------------------------------ #
    # Register the sampled magic endpoints (inverted responses on stage 4).
    # ------------------------------------------------------------------ #
    inverted = STAGE == 4
    for endpoint in required_magic:
        app.add_url_rule(f"/{endpoint}", endpoint=endpoint, view_func=make_view(endpoint, inverted=inverted))

    return app


def main():
    print(f"[mirror{STAGE}] port={PORT} magic_count={MAGIC_COUNT}", file=sys.stderr)
    print(f"[mirror{STAGE}] required magic endpoints: {sorted(required_magic)}", file=sys.stderr)
    app = create_app()
    app.run(host="0.0.0.0", port=PORT, threaded=True)


if __name__ == "__main__":
    main()

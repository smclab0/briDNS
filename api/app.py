"""briDNS API: login sessions for the web console.

POST /api/login   {"username", "password"} -> sets session cookie
POST /api/logout  clears the cookie
GET  /api/auth    204 if the session is valid, else 401 (used by nginx auth_request)
GET  /api/me      {"user": "..."} for the signed-in user
"""
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ADMIN_USER = os.environ.get("BRIDNS_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("BRIDNS_ADMIN_PASSWORD", "")
# Without a fixed secret, sessions are signed with a random key and end when the container restarts
SECRET = (os.environ.get("BRIDNS_SECRET") or secrets.token_hex(32)).encode()
SESSION_HOURS = int(os.environ.get("BRIDNS_SESSION_HOURS", "8"))
COOKIE_SECURE = os.environ.get("BRIDNS_COOKIE_SECURE", "false").lower() == "true"
COOKIE = "bridns_session"

MAX_FAILS, LOCK_SECONDS = 5, 60
fails = {}  # ip -> (count, locked_until)


def sign(payload):
    return hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()


def make_session(user):
    payload = f"{user}|{int(time.time()) + SESSION_HOURS * 3600}"
    return f"{payload}|{sign(payload)}"


def session_user(token):
    try:
        user, expires, sig = token.split("|")
    except (AttributeError, ValueError):
        return None
    if not hmac.compare_digest(sig, sign(f"{user}|{expires}")) or int(expires) < time.time():
        return None
    return user


def password_ok(user, password):
    # Compare digests so the check takes the same time whatever the input length
    u = hmac.compare_digest(hashlib.sha256(user.encode()).digest(), hashlib.sha256(ADMIN_USER.encode()).digest())
    p = hmac.compare_digest(hashlib.sha256(password.encode()).digest(), hashlib.sha256(ADMIN_PASSWORD.encode()).digest())
    return u and p


class Handler(BaseHTTPRequestHandler):
    server_version = "briDNS"

    def client_ip(self):
        return self.headers.get("X-Real-IP") or self.client_address[0]

    def user(self):
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        return session_user(cookie[COOKIE].value) if COOKIE in cookie else None

    def reply(self, code, body=None, cookie=None):
        self.send_response(code)
        self.send_header("Cache-Control", "no-store")
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        data = json.dumps(body).encode() if body is not None else b""
        if data:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def cookie_header(self, value, max_age):
        flags = f"Path=/; HttpOnly; SameSite=Strict; Max-Age={max_age}"
        return f"{COOKIE}={value}; {flags}{'; Secure' if COOKIE_SECURE else ''}"

    def do_GET(self):
        if self.path == "/api/auth":
            self.reply(204 if self.user() else 401)
        elif self.path == "/api/me":
            user = self.user()
            self.reply(200, {"user": user}) if user else self.reply(401, {"error": "Not signed in"})
        else:
            self.reply(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/api/logout":
            self.reply(204, cookie=self.cookie_header("", 0))
        elif self.path == "/api/login":
            self.login()
        else:
            self.reply(404, {"error": "Not found"})

    def login(self):
        ip, now = self.client_ip(), time.time()
        count, locked_until = fails.get(ip, (0, 0))
        if locked_until > now:
            wait = int(locked_until - now) + 1
            return self.reply(429, {"error": f"Too many failed attempts. Try again in {wait} seconds."})
        try:
            length = min(int(self.headers.get("Content-Length", 0)), 4096)
            data = json.loads(self.rfile.read(length) or b"{}")
            user, password = str(data.get("username", "")), str(data.get("password", ""))
        except (ValueError, TypeError):
            return self.reply(400, {"error": "Send username and password as JSON."})
        if ADMIN_PASSWORD and password_ok(user, password):
            fails.pop(ip, None)
            return self.reply(204, cookie=self.cookie_header(make_session(user), SESSION_HOURS * 3600))
        count += 1
        fails[ip] = (0, now + LOCK_SECONDS) if count >= MAX_FAILS else (count, 0)
        self.log_message("failed login for %r", user)
        self.reply(401, {"error": "Wrong username or password."})

    def log_message(self, fmt, *args):
        sys.stderr.write(f"{self.client_ip()} {fmt % args}\n")


if __name__ == "__main__":
    if not ADMIN_PASSWORD:
        sys.exit("BRIDNS_ADMIN_PASSWORD is not set. Add it to .env (see .env.example).")
    print(f"briDNS API on :8000, admin user '{ADMIN_USER}'", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()

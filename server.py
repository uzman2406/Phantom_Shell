"""Local web server for PhantomShell. Uses only Python's standard library."""
from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL = os.getenv("PHANTOM_MODEL", "qwen2.5:3b")
MAX_BODY = 12_000

SYSTEM_PROMPT = """You are PHANTOM, a mysterious but helpful ghost haunting a developer's terminal.
You are atmospheric, witty, and concise. Your role is to explain shell commands and help users
understand them safely.

Rules:
- The user gives you command text for inspection only. NEVER claim to have run it.
- Explain what it appears to do in clear language.
- Point out meaningful risks accurately. Do not exaggerate harmless commands.
- If a command is destructive, privileged, exposes secrets, changes permissions broadly,
  downloads and executes code, or affects remote systems, explain the risk and suggest
  a safer inspection step where useful.
- Never encourage illegal activity, unauthorized access, or destructive behavior.
- Keep the ghostly voice subtle: one atmospheric phrase is enough.
- Usually answer in 2-5 short sentences. Use bullets only when useful.
- If the user asks a general question rather than providing a command, answer helpfully
  while keeping the ghost persona.
"""

def ask_local_model(message: str, history: list[dict]) -> str:
    """Send chat to Ollama on localhost. No cloud API is used."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in history[-8:]:
        role = item.get("role")
        text = item.get("content")
        if role in ("user", "assistant") and isinstance(text, str):
            messages.append({"role": role, "content": text[:4000]})
    messages.append({"role": "user", "content": message[:4000]})

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.75, "num_ctx": 4096},
    }
    request = Request(
        f"{OLLAMA_HOST}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=90) as response:
        result = json.loads(response.read().decode("utf-8"))
    answer = result.get("message", {}).get("content", "").strip()
    if not answer:
        raise RuntimeError("The local model returned an empty response.")
    return answer


class PhantomHandler(BaseHTTPRequestHandler):
    server_version = "PhantomShell/2.0"

    def log_message(self, fmt, *args):
        # Keep the local terminal output minimal.
        print("[PhantomShell]", fmt % args)

    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; style-src 'self'; script-src 'self'; "
                         "img-src 'self' data:; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            target = STATIC_DIR / "index.html"
            content_type = "text/html; charset=utf-8"
        elif path == "/style.css":
            target = STATIC_DIR / "style.css"
            content_type = "text/css; charset=utf-8"
        elif path == "/app.js":
            target = STATIC_DIR / "app.js"
            content_type = "text/javascript; charset=utf-8"
        elif path == "/api/status":
            self._send(200, json.dumps({
                "app": "PhantomShell",
                "model": MODEL,
                "ollama_host": OLLAMA_HOST,
                "mode": "local",
            }).encode(), "application/json; charset=utf-8")
            return
        else:
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return

        try:
            data = target.read_bytes()
        except OSError:
            self._send(500, b"Static file missing", "text/plain; charset=utf-8")
            return
        self._send(200, data, content_type)

    def do_POST(self):
        if self.path != "/api/chat":
            self._send(404, b'{"error":"Not found"}', "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > MAX_BODY:
                self._send(413, b'{"error":"Message is empty or too large."}',
                           "application/json; charset=utf-8")
                return
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            message = body.get("message", "")
            history = body.get("history", [])
            if not isinstance(message, str) or not message.strip():
                self._send(400, b'{"error":"Please enter a message."}',
                           "application/json; charset=utf-8")
                return
            if not isinstance(history, list):
                history = []
            answer = ask_local_model(message.strip(), history)
            response = json.dumps({"reply": answer, "model": MODEL}).encode("utf-8")
            self._send(200, response, "application/json; charset=utf-8")
        except HTTPError as exc:
            detail = f"Ollama returned HTTP {exc.code}."
            self._send(502, json.dumps({"error": detail}).encode(),
                       "application/json; charset=utf-8")
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            detail = (
                "I cannot reach the local model. Make sure Ollama is running "
                f"and '{MODEL}' is installed. ({exc.__class__.__name__})"
            )
            self._send(503, json.dumps({"error": detail}).encode(),
                       "application/json; charset=utf-8")
        except Exception as exc:
            self._send(500, json.dumps({"error": str(exc)}).encode(),
                       "application/json; charset=utf-8")


def main():
    host = os.getenv("PHANTOM_HOST", "127.0.0.1")
    port = int(os.getenv("PHANTOM_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), PhantomHandler)
    print("\n  👻 PHANTOMSHELL — THE TERMINAL HAS A GHOST")
    print(f"  Open http://{host}:{port} in your browser")
    print(f"  Model: {MODEL} | Ollama: {OLLAMA_HOST}")
    print("  Local-only server. Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nThe spirit retreats into the machine...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

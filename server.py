# -*- coding: utf-8 -*-
"""Servidor local del gestor de tickets. Solo libreria estandar.

Datos en data/tickets.json y data/contacts.json. Variables de entorno: PORT (8791), HOST (127.0.0.1),
DATA_DIR (./data) para cuando se pase a Docker.
"""
import json
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE, "data"))
COLLECTIONS = ("tickets", "contacts")
LOCK = threading.Lock()
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
KEEP_DAILY = 30


def load(col):
    path = os.path.join(DATA_DIR, col + ".json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(col, items):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, col + ".json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def snapshot(name=None):
    """Copia de seguridad: una por dia (la primera del dia) o con nombre explicito."""
    name = name or "backup-%s.json" % time.strftime("%Y-%m-%d")
    path = os.path.join(BACKUP_DIR, name)
    if os.path.exists(path):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"tickets": load("tickets"), "contacts": load("contacts")}, f, ensure_ascii=False)
    daily = sorted(n for n in os.listdir(BACKUP_DIR) if n.startswith("backup-"))
    for old in daily[:-KEEP_DAILY]:
        os.remove(os.path.join(BACKUP_DIR, old))


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _route(self):
        m = re.fullmatch(r"/api/(tickets|contacts)/([\w-]+)", self.path)
        return (m.group(1), m.group(2)) if m else (None, None)

    def do_GET(self):
        m = re.fullmatch(r"/api/(tickets|contacts)", self.path)
        if m:
            with LOCK:
                return self._json(load(m.group(1)))
        if self.path == "/api/export":
            with LOCK:
                data = {"exported": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "tickets": load("tickets"), "contacts": load("contacts")}
            body = json.dumps(data, ensure_ascii=False, indent=1).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition",
                             'attachment; filename="tickets-%s.json"' % time.strftime("%Y-%m-%d"))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path in ("/", "/index.html"):
            with open(os.path.join(STATIC, "index.html"), "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._json({"error": "no encontrado"}, 404)

    def do_POST(self):
        if self.path != "/api/import":
            return self._json({"error": "ruta invalida"}, 404)
        n = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(n).decode("utf-8"))
            tickets, contacts = data["tickets"], data.get("contacts", [])
            assert isinstance(tickets, list) and isinstance(contacts, list)
            assert all(isinstance(x, dict) and x.get("id") for x in tickets + contacts)
        except (ValueError, KeyError, AssertionError, TypeError):
            return self._json({"error": "fichero de copia invalido"}, 400)
        with LOCK:
            snapshot("pre-import-%s.json" % time.strftime("%Y-%m-%d-%H%M%S"))
            save("tickets", tickets)
            save("contacts", contacts)
        self._json({"ok": True, "tickets": len(tickets), "contacts": len(contacts)})

    def do_PUT(self):
        col, tid = self._route()
        if not tid:
            return self._json({"error": "ruta invalida"}, 404)
        n = int(self.headers.get("Content-Length", 0))
        try:
            ticket = json.loads(self.rfile.read(n).decode("utf-8"))
        except ValueError:
            return self._json({"error": "json invalido"}, 400)
        ticket["id"] = tid
        with LOCK:
            snapshot()
            items = load(col)
            for i, t in enumerate(items):
                if t["id"] == tid:
                    items[i] = ticket
                    break
            else:
                items.append(ticket)
            save(col, items)
        self._json({"ok": True})

    def do_DELETE(self):
        col, tid = self._route()
        if not tid:
            return self._json({"error": "ruta invalida"}, 404)
        with LOCK:
            snapshot()
            save(col, [t for t in load(col) if t["id"] != tid])
        self._json({"ok": True})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8791"))
    with LOCK:
        snapshot()
    print("Gestor de tickets en http://%s:%d" % (host, port))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
